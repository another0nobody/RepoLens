"""一次分析的完整流程（编排层）。

server.py 只负责"收 HTTP 请求、推 SSE"，真正干活的是本文件：

    1. 检查模型配置；
    2. 创建 Agent；
    3. 用 agent.stream 跑 Agent，同时把事件转发给网页；
    4. 处理 Human-in-the-loop 的中断/恢复；
    5. 拿到结构化结果，合并成报告并保存；
    6. 任何一步失败，都尽量降级成"规则扫描报告"，而不是让页面白屏。

【给初学者：为什么要有"降级"？】
真实项目里，网络会断、模型会抽风、用户可能没填 API Key。
一个可靠的 Agent 应用，应该在 AI 不可用时仍然给出"能用的结果"，
并明确告诉用户"这部分是 AI 生成的，那部分是规则扫描的"。
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Iterator

from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.types import Command

from . import config
from .agent import (
    build_analysis_agent,
    build_chat_agent,
    build_task_prompt,
    summarize_interrupt,
)
from .context import AnalysisContext
from .report import build_report, save_report
from .scanner import scan_repository
from .sources import SourceError, validate_local_path
from .tools import repo_overview

# 等用户点"批准/拒绝"的最长时间（秒）
HITL_TIMEOUT = 300


def run_analysis(ctx: AnalysisContext) -> None:
    """后台线程入口：跑完整分析流程，事件全部通过 ctx.emit 推送。"""
    started = time.time()
    ctx.emit(
        "started",
        {
            "run_id": ctx.run_id,
            "source": ctx.source,
            "source_type": ctx.source_type,
            "model": ctx.model_display,
        },
    )
    ctx.emit("phase", {"stage": "prepare", "label": "检查模型与运行环境"})

    cfg = config.load_model_config()
    ctx.model_display = cfg.display_name
    ai_error: str | None = None
    insight: Any = None

    if not cfg.available:
        ai_error = "没有配置大模型 API Key，本次仅使用规则扫描"
        ctx.emit("warning", {"message": ai_error, "hint": "在 .env 中填入 GLM_API_KEY 或 DEEPSEEK_API_KEY 后可启用 AI 解读"})
        ctx.log(ai_error, "warning")
    else:
        try:
            ctx.emit("phase", {"stage": "init", "label": "初始化 LangChain Agent"})
            ctx.log(f"使用模型：{cfg.display_name}")
            agent = build_analysis_agent(ctx)
            insight = _run_agent(agent, ctx)
        except Exception as exc:  # noqa: BLE001 - 任何异常都要变成可读信息
            ai_error = f"{type(exc).__name__}: {exc}"
            ctx.log(f"AI 分析失败，将使用规则扫描兜底：{ai_error}", "error")
            ctx.emit("warning", {"message": "AI 分析失败，已切换为规则扫描", "detail": ai_error[:500]})
            traceback.print_exc()

    # 如果 Agent 因为报错/限流等原因没能准备好仓库，这里再兜底扫描一次本地目录。
    if ctx.snapshot is None:
        _fallback_scan(ctx)

    if ctx.snapshot is None:
        message = ctx.error or ai_error or "分析失败：没有拿到仓库内容"
        ctx.emit("error", {"message": message, "detail": ai_error})
        ctx.log(message, "error")
        ctx.finish()
        return

    try:
        ctx.emit("phase", {"stage": "report", "label": "合并扫描事实与 AI 解读"})
        report = build_report(ctx, insight, ai_error)
        save_report(report)
    except Exception as exc:  # noqa: BLE001
        message = f"生成报告失败：{exc}"
        ctx.emit("error", {"message": message})
        ctx.log(message, "error")
        traceback.print_exc()
        ctx.finish()
        return

    ctx.report = report
    ctx.emit(
        "phase",
        {
            "stage": "done",
            "label": "报告已生成",
            "duration": round(time.time() - started, 1),
        },
    )
    ctx.emit(
        "done",
        {
            "run_id": ctx.run_id,
            "repo_name": report["repo_name"],
            "tech_count": len(report["techs"]),
            "ai_used": report["ai"]["used"],
            "duration": round(time.time() - started, 1),
        },
    )
    ctx.finish()


# ============================================================================
# 运行 Agent + 流式事件
# ============================================================================
def _run_agent(agent: Any, ctx: AnalysisContext) -> Any:
    """真正跑 Agent 的循环，返回 structured_response（可能为 None）。"""
    config_ = {
        "configurable": {"thread_id": ctx.run_id},
        # 注意：LangGraph 的 recursion_limit 统计的是"图节点步数"，
        # 每个中间件钩子都会算一步，所以这里要给得宽裕一些（不是模型调用次数）。
        # 真正的模型调用次数由 ModelCallLimitMiddleware 控制。
        "recursion_limit": 250,
    }
    payload: Any = {
        "messages": [HumanMessage(content=build_task_prompt(ctx))],
        "run_id": ctx.run_id,
        "user_id": "local-user",
    }

    for attempt in range(6):
        interrupted = False
        ctx.emit(
            "phase",
            {
                "stage": "agent",
                "label": "Agent 正在分析仓库" if attempt == 0 else "继续执行（已获得授权）",
            },
        )
        stream = agent.stream(
            payload,
            config=config_,
            stream_mode=["updates", "custom"],
        )
        for mode, chunk in stream:
            if mode == "custom":
                _handle_custom(ctx, chunk)
            elif mode == "updates":
                if _handle_updates(ctx, chunk):
                    interrupted = True

        if not interrupted:
            break

        decision = _wait_human_decision(ctx)
        ctx.interrupt_payload = None
        if decision is None:
            ctx.error = "等待克隆批准超时，本次分析已停止"
            break
        if decision.get("type") != "approve":
            # 拒绝克隆后立即结束，不再让模型反复重试同一个被拒绝的工具。
            ctx.error = decision.get("message") or "你拒绝了克隆操作，本次分析已停止"
            break
        payload = Command(resume={"decisions": [decision]})

    snapshot = agent.get_state(config_)
    values = snapshot.values or {}
    return values.get("structured_response")


def _handle_custom(ctx: AnalysisContext, chunk: Any) -> None:
    """处理工具里通过 get_stream_writer 发来的 custom 消息。"""
    if isinstance(chunk, dict):
        if chunk.get("type") == "progress":
            ctx.emit(
                "progress",
                {
                    "message": chunk.get("message", ""),
                    "percent": chunk.get("percent"),
                },
            )
        else:
            ctx.emit("custom", chunk)
    else:
        ctx.emit("progress", {"message": str(chunk)})


def _handle_updates(ctx: AnalysisContext, chunk: Any) -> bool:
    """处理 LangGraph 的状态更新。

    返回 True 表示这次更新里包含"中断"（等人类批准）。
    """
    if not isinstance(chunk, dict):
        return False

    interrupts = chunk.get("__interrupt__")
    if interrupts:
        interrupt = interrupts[0]
        value = getattr(interrupt, "value", interrupt)
        payload = summarize_interrupt(value)
        pending = {
            **payload,
            "id": str(getattr(interrupt, "id", "")),
            "timeout": HITL_TIMEOUT,
        }
        ctx.interrupt_payload = pending
        ctx.emit("interrupt", pending)
        ctx.log("已暂停：等待你批准克隆 GitHub 仓库", "warning")
        return True

    for node, update in chunk.items():
        if not isinstance(update, dict):
            continue
        todos = update.get("todos")
        if todos:
            ctx.emit("todos", {"todos": todos})

        if node == "model" or node.endswith(".model"):
            for message in update.get("messages") or []:
                if isinstance(message, AIMessageChunk):
                    content = message.content
                    if isinstance(content, str) and content.strip():
                        ctx.emit("assistant", {"content": content.strip()[:600]})
    return False


def _wait_human_decision(ctx: AnalysisContext) -> dict | None:
    """阻塞等待网页上的批准/拒绝。超时或取消时返回 None。"""
    ctx.emit(
        "phase",
        {"stage": "waiting_human", "label": "等待你确认是否克隆仓库"},
    )
    decision = ctx.wait_for_decision(timeout=HITL_TIMEOUT)
    if decision is None:
        ctx.log("等待超时，将自动拒绝本次克隆", "warning")
        ctx.emit("interrupt_resolved", {"decision": "timeout"})
        return None
    decision_type = decision.get("type", "reject")
    ctx.emit("interrupt_resolved", {"decision": decision_type})
    if decision_type == "approve":
        ctx.log("你已批准克隆，继续分析", "info")
        return {"type": "approve"}
    reason = decision.get("message") or "用户拒绝了克隆操作"
    ctx.log(f"你已拒绝克隆：{reason}", "warning")
    return {"type": "reject", "message": reason}


# ============================================================================
# 兜底扫描
# ============================================================================
def _fallback_scan(ctx: AnalysisContext) -> None:
    """当 Agent 没能调用扫描工具时，用纯规则扫描再试一次。"""
    if ctx.snapshot is not None:
        return
    if ctx.source_type != "local":
        if ctx.error is None:
            ctx.error = "GitHub 仓库没有准备好（可能未获得克隆授权或网络失败）"
        return
    try:
        ctx.emit("phase", {"stage": "fallback", "label": "用规则扫描兜底"})
        path = validate_local_path(ctx.source)
        ctx.progress("AI 未能完成仓库准备，改用规则扫描…")
        snapshot = scan_repository(
            root=path,
            source=ctx.source,
            source_type="local",
            progress=lambda message: ctx.progress(message),
        )
        ctx.repo_root = path
        ctx.snapshot = snapshot
        ctx.source_note = "本地目录（规则扫描兜底）"
        ctx.emit("meta", repo_overview(snapshot, ctx.source_note))
    except Exception as exc:  # noqa: BLE001
        ctx.error = str(exc)
        ctx.log(f"兜底扫描也失败了：{exc}", "error")


# ============================================================================
# 追问
# ============================================================================
def stream_chat(ctx: AnalysisContext, message: str, agent: Any = None) -> Iterator[dict]:
    """以生成器的方式产出聊天事件，server.py 负责写成 SSE。

    事件类型：
        {"type": "meta", "data": {...}}    开始
        {"type": "token", "data": {"text": "..."}}  逐字输出
        {"type": "tool", "data": {...}}    工具调用提示
        {"type": "done", "data": {...}}   结束
        {"type": "error", "data": {...}}  出错
    """
    if ctx.report is None:
        yield {"type": "error", "data": {"message": "还没有生成报告，无法追问。"}}
        return
    cfg = config.load_model_config()
    if not cfg.available:
        yield {
            "type": "error",
            "data": {"message": "没有配置大模型 API Key，无法使用追问功能。请先在 .env 中填入密钥。"},
        }
        return

    try:
        if agent is None:
            agent = build_chat_agent(ctx)
        config_ = {"configurable": {"thread_id": f"chat-{ctx.run_id}"}, "recursion_limit": 60}
        yield {"type": "meta", "data": {"model": cfg.display_name}}

        for mode, chunk in agent.stream(
            {"messages": [HumanMessage(content=message)]},
            config=config_,
            stream_mode=["messages", "updates"],
        ):
            if mode == "messages":
                message_chunk, metadata = chunk
                if not isinstance(message_chunk, AIMessageChunk):
                    continue
                node = (metadata or {}).get("langgraph_node", "")
                if "model" not in str(node):
                    continue
                content = message_chunk.content
                if isinstance(content, str) and content:
                    yield {"type": "token", "data": {"text": content}}
            elif mode == "updates" and isinstance(chunk, dict):
                for node, update in chunk.items():
                    if not isinstance(update, dict):
                        continue
                    for item in update.get("messages") or []:
                        tool_calls = getattr(item, "tool_calls", None) or []
                        for call in tool_calls:
                            if call.get("name"):
                                yield {
                                    "type": "tool",
                                    "data": {
                                        "name": call.get("name"),
                                        "args": call.get("args", {}),
                                    },
                                }
        yield {"type": "done", "data": {"ok": True}}
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        yield {"type": "error", "data": {"message": f"追问失败：{exc}"}}
