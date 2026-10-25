"""自定义中间件（Middleware）。

【给初学者：中间件是什么？】
Agent 的一次运行会经过几个固定节点：开始 -> 模型思考 -> 调用工具 -> 模型思考 -> … -> 结束。
中间件就是"挂在节点上的钩子函数"，让你在不修改 Agent 主流程的前提下：
    - 在模型调用前后做点事（before_model / after_model）；
    - 在工具调用前后做点事（wrap_tool_call）；
    - 修改发给模型的消息、拦截工具结果、甚至强制跳转。

本文件有两个中间件：
    1. ProgressMiddleware：把 Agent 的每一步变成网页上的进度条/时间线；
    2. SecretMaskingMiddleware：在工具结果交给模型前，把疑似密钥打码。

教程里还演示了 HumanInTheLoopMiddleware、TodoListMiddleware、SummarizationMiddleware
等内置中间件，它们直接在 agent.py 里使用，不需要自己写。
"""

from __future__ import annotations

import time
from typing import Any, Callable

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import Command

from .context import AnalysisContext
from .security import mask_secrets


class ProgressMiddleware(AgentMiddleware):
    """把 Agent 的执行过程实时推给网页。

    这是"自定义中间件"的典型用法：业务代码（Agent）不用关心 UI，
    UI 也不需要侵入 Agent，双方通过事件总线解耦。
    """

    def __init__(self, ctx: AnalysisContext) -> None:
        super().__init__()
        self.ctx = ctx
        self._model_calls = 0

    # ------------------------------------------------------------ 模型钩子
    def before_model(self, state: Any, runtime: Any) -> dict[str, Any] | None:
        """每次调用大模型之前触发。"""
        self._model_calls += 1
        self.ctx.emit("phase", {"stage": "reasoning", "label": "模型正在思考与规划"})
        self.ctx.emit(
            "model",
            {"status": "start", "call": self._model_calls, "message": "正在调用大模型…"},
        )
        return None

    def after_model(self, state: Any, runtime: Any) -> dict[str, Any] | None:
        """模型返回之后触发：汇报它打算调用哪些工具、消耗了多少 token。"""
        messages = state.get("messages") or []
        if not messages:
            return None
        last = messages[-1]
        if not isinstance(last, AIMessage):
            return None

        usage = getattr(last, "usage_metadata", None) or {}
        if usage:
            input_tokens = int(usage.get("input_tokens") or 0)
            output_tokens = int(usage.get("output_tokens") or 0)
            self.ctx.token_usage["input"] += input_tokens
            self.ctx.token_usage["output"] += output_tokens
            self.ctx.emit(
                "tokens",
                {
                    "input": self.ctx.token_usage["input"],
                    "output": self.ctx.token_usage["output"],
                    "last_input": input_tokens,
                    "last_output": output_tokens,
                },
            )

        tool_calls = getattr(last, "tool_calls", None) or []
        if tool_calls:
            planned = []
            for call in tool_calls:
                name = call.get("name", "")
                if name in {"write_todos", "Report", "RepoInsight"}:
                    continue
                planned.append({"name": name, "args": call.get("args", {})})
            if planned:
                self.ctx.emit("plan", {"tools": planned})
        else:
            text = last.content if isinstance(last.content, str) else ""
            if text.strip():
                self.ctx.emit("model", {"status": "text", "message": text.strip()[:500]})
        return None

    # ------------------------------------------------------------ 工具钩子
    def wrap_tool_call(
        self,
        request: Any,
        handler: Callable[[Any], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        """包住一次工具调用：开始前发事件，结束后发耗时和结果预览。"""
        tool_call = getattr(request, "tool_call", {}) or {}
        name = tool_call.get("name", "unknown")
        args = tool_call.get("args", {}) or {}
        friendly = TOOL_LABELS.get(name, name)
        started = time.time()

        self.ctx.emit(
            "tool",
            {
                "name": name,
                "label": friendly,
                "status": "start",
                "args": _short_args(args),
                "message": f"正在调用「{friendly}」…",
            },
        )
        try:
            result = handler(request)
        except Exception as exc:
            self.ctx.emit(
                "tool",
                {
                    "name": name,
                    "label": friendly,
                    "status": "error",
                    "message": f"「{friendly}」执行失败：{exc}",
                    "duration": round(time.time() - started, 2),
                },
            )
            raise

        preview = ""
        if isinstance(result, ToolMessage):
            content = result.content
            if isinstance(content, str):
                preview = content[:600]
        self.ctx.emit(
            "tool",
            {
                "name": name,
                "label": friendly,
                "status": "end",
                "duration": round(time.time() - started, 2),
                "preview": preview,
                "message": f"「{friendly}」完成，用时 {time.time() - started:.1f} 秒",
            },
        )
        return result

    # ------------------------------------------------------------ 生命周期
    def before_agent(self, state: Any, runtime: Any) -> dict[str, Any] | None:
        self.ctx.emit("phase", {"stage": "start", "label": "开始分析"})
        return None

    def after_agent(self, state: Any, runtime: Any) -> dict[str, Any] | None:
        self.ctx.emit("phase", {"stage": "finishing", "label": "整理分析结论"})
        return None


class SecretMaskingMiddleware(AgentMiddleware):
    """工具返回结果 -> 模型之前，做一次"密钥打码"。

    为什么不在工具里做？因为有些工具是框架自带的（比如文件搜索），
    统一在中间件里处理，能覆盖所有工具，而且只写一次。
    """

    def __init__(self, ctx: AnalysisContext) -> None:
        super().__init__()
        self.ctx = ctx
        self._reported = 0

    def wrap_tool_call(
        self,
        request: Any,
        handler: Callable[[Any], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        result = handler(request)
        if isinstance(result, ToolMessage) and isinstance(result.content, str):
            masked, hits = mask_secrets(result.content)
            if hits:
                result.content = masked
                self._reported += hits
                self.ctx.log(f"已在工具结果中隐藏 {self._reported} 处疑似敏感信息", "warning")
        return result


TOOL_LABELS = {
    "write_todos": "更新任务清单",
    "clone_github_repository": "克隆 GitHub 仓库",
    "inspect_local_repository": "扫描本地仓库",
    "list_technologies": "列出技术候选",
    "inspect_technology": "核实技术与模块",
    "read_project_file": "读取项目文件",
    "remember_analysis": "写入长期记忆",
    "report_overview": "读取报告摘要",
    "search_report": "检索报告",
    "explain_technology": "查看技术详情",
    "technology_deep_dive": "技术深挖",
}


def _short_args(args: dict) -> dict:
    """把工具参数截短，避免网页被一大段 JSON 撑爆。"""
    short: dict = {}
    for key, value in list(args.items())[:6]:
        if isinstance(value, str):
            short[key] = value[:120]
        elif isinstance(value, list):
            short[key] = [str(item)[:60] for item in value[:6]]
        else:
            short[key] = value
    return short
