"""零第三方依赖的 Web 服务器（只用 Python 标准库）。

【给初学者：为什么不用 FastAPI？】
FastAPI 很好，但本项目希望"下载下来就能跑"：
你只需要 Python + LangChain，不需要再安装 Web 框架。
Python 自带的 http.server 虽然朴素，但足够支撑：
    - 提供网页静态文件；
    - 提供 JSON API；
    - 用 SSE（Server-Sent Events）把 Agent 的进度实时推给浏览器。

如果你以后要部署到生产环境，把本文件换成 FastAPI/Flask 是很自然的升级。

【接口一览】
    GET  /                      网页
    GET  /static/*              静态资源
    GET  /api/health            服务与模型状态
    GET  /api/examples          示例仓库
    POST /api/analyze           开始一次分析 -> {run_id}
    GET  /api/events?run_id=    分析进度（SSE 流）
    POST /api/hitl              批准/拒绝克隆
    GET  /api/report?run_id=    读取报告
    GET  /api/history           历史报告
    GET  /api/memory            长期记忆
    POST /api/chat              追问（SSE 流式回答）
"""

from __future__ import annotations

import json
import mimetypes
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.store.memory import InMemoryStore

from . import __version__, config
from .context import AnalysisContext
from .events import EventBus
from .pipeline import run_analysis, stream_chat
from .report import list_reports, load_report
from .scanner import MAX_FILES
from .sources import SourceError, looks_like_github, parse_github, validate_local_path

STATIC_DIR = config.PROJECT_ROOT / "static"
MAX_ACTIVE_RUNS = 2


class TooManyRuns(RuntimeError):
    """同时分析的任务太多。"""


@dataclass
class Run:
    """一次运行在服务器端的状态。"""

    run_id: str
    source: str
    source_type: str
    ctx: AnalysisContext
    thread: threading.Thread | None = None
    status: str = "running"  # running / done / error
    created_at: float = field(default_factory=time.time)
    chat_agent: Any = None
    chat_lock: threading.Lock = field(default_factory=threading.Lock)


class RepoLensApp:
    """把"运行管理"和"报告读取"从 HTTP 细节里拆出来。"""

    def __init__(self) -> None:
        self.runs: dict[str, Run] = {}
        self.lock = threading.Lock()
        # 结构化输出结果会被序列化进 checkpoint。显式允许我们自己的 Pydantic 类型，
        # 否则新版 LangGraph 会给出 "unregistered type" 警告，未来版本可能直接拒绝。
        # 这里做一层兼容：万一某个 LangGraph 版本没有这个序列化器，也能正常启动。
        try:
            serde = JsonPlusSerializer(
                allowed_msgpack_modules=[
                    ("repolens.schemas", "RepoInsight"),
                    ("repolens.schemas", "TechFinding"),
                ]
            )
            self.checkpointer = InMemorySaver(serde=serde)
        except Exception:
            self.checkpointer = InMemorySaver()
        self.store = InMemoryStore()
        config.REPOS_DIR.mkdir(parents=True, exist_ok=True)
        config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.started_at = time.time()

    # ------------------------------------------------------------------ 运行
    def start_run(self, source: str) -> Run:
        source = source.strip()
        if not source:
            raise SourceError("请输入本地仓库路径或 GitHub 地址。")
        if len(source) > 500:
            raise SourceError("输入的路径/地址太长了。")

        if looks_like_github(source):
            parse_github(source)  # 只校验格式，真正的克隆交给 Agent 工具
            source_type = "github"
        else:
            validate_local_path(source)  # 本地路径尽早检查，失败可以立刻提示
            source_type = "local"

        with self.lock:
            active = [run for run in self.runs.values() if run.status == "running"]
            if len(active) >= MAX_ACTIVE_RUNS:
                raise TooManyRuns("同时最多分析 2 个仓库，请等待当前任务完成。")
            # 只保留最近 30 个运行的内存状态，避免进程越跑越大。
            if len(self.runs) > 30:
                finished = sorted(
                    (run for run in self.runs.values() if run.status != "running"),
                    key=lambda run: run.created_at,
                )
                for old in finished[:10]:
                    self.runs.pop(old.run_id, None)

            run_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
            bus = EventBus(run_id)
            cfg = config.load_model_config()
            ctx = AnalysisContext(
                run_id=run_id,
                source=source,
                source_type=source_type,
                bus=bus,
                store=self.store,
                checkpointer=self.checkpointer,
                model_display=cfg.display_name,
            )
            run = Run(run_id=run_id, source=source, source_type=source_type, ctx=ctx)
            self.runs[run_id] = run

        run.thread = threading.Thread(
            target=self._run_thread,
            args=(run,),
            name=f"analysis-{run_id}",
            daemon=True,
        )
        run.thread.start()
        return run

    def _run_thread(self, run: Run) -> None:
        try:
            run_analysis(run.ctx)
        except Exception as exc:  # noqa: BLE001 - 后台线程必须兜住所有异常
            run.ctx.emit("error", {"message": f"分析线程异常：{exc}"})
            run.ctx.finish()
        finally:
            run.status = "done" if run.ctx.report else "error"

    def get_run(self, run_id: str) -> Run | None:
        with self.lock:
            return self.runs.get(run_id)

    def get_report(self, run_id: str) -> dict | None:
        run = self.get_run(run_id)
        if run is not None and run.ctx.report is not None:
            return run.ctx.report
        return load_report(run_id)

    def ensure_run_for_report(self, run_id: str, report: dict) -> Run:
        """从磁盘加载历史报告后，临时重建一个上下文，让"追问"仍然可用。"""
        run = self.get_run(run_id)
        if run is not None:
            return run
        bus = EventBus(run_id)
        bus.close()
        ctx = AnalysisContext(
            run_id=run_id,
            source=str(report.get("source", "")),
            source_type=str(report.get("source_type", "local")),
            bus=bus,
            store=self.store,
            checkpointer=self.checkpointer,
            model_display=str((report.get("ai") or {}).get("model", "")),
        )
        ctx.report = report
        ctx.source_note = str(report.get("source_note", ""))
        local_path = report.get("local_path")
        if local_path and Path(local_path).is_dir():
            ctx.repo_root = Path(local_path)
        run = Run(
            run_id=run_id,
            source=ctx.source,
            source_type=ctx.source_type,
            ctx=ctx,
            status="done",
        )
        with self.lock:
            self.runs[run_id] = run
        return run

    # ------------------------------------------------------------------ 其他
    def health(self) -> dict:
        cfg = config.load_model_config()
        return {
            "ok": True,
            "app": "RepoLens",
            "version": __version__,
            "model": cfg.display_name,
            "ai_available": cfg.available,
            "provider": cfg.provider,
            "uptime_seconds": int(time.time() - self.started_at),
            "active_runs": len([run for run in self.runs.values() if run.status == "running"]),
            "max_files": MAX_FILES,
        }

    def examples(self) -> list[dict]:
        # 用相对路径，避免把本机绝对路径暴露给浏览器；启动时会按项目根目录解析。
        items = [
            {
                "label": "内置示例仓库",
                "value": "examples/demo_shop",
                "kind": "local",
                "description": "FastAPI + React + PostgreSQL + Docker 的小型商城",
            },
            {
                "label": "本项目核心代码",
                "value": "repolens",
                "kind": "local",
                "description": "RepoLens 的 Python 包：LangChain + LangGraph + 原生 Web",
            },
            {
                "label": "GitHub 示例",
                "value": "https://github.com/psf/requests",
                "kind": "github",
                "description": "Python 经典 HTTP 库，适合观察 GitHub 克隆 + 审批流程",
            },
        ]
        return items

    def memory_items(self) -> list[dict]:
        items: list[dict] = []
        try:
            for item in self.store.search(("repolens", "analyses")):
                value = getattr(item, "value", {}) or {}
                items.append(
                    {
                        "key": getattr(item, "key", ""),
                        "value": value,
                        "updated_at": str(getattr(item, "updated_at", "")),
                    }
                )
        except Exception:
            return []
        items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return items[:20]


# ============================================================================
# HTTP 处理
# ============================================================================
class RepoLensHandler(BaseHTTPRequestHandler):
    server_version = f"RepoLens/{__version__}"
    protocol_version = "HTTP/1.0"  # 用短连接，SSE 实现更简单，本地使用足够

    # ------------------------------------------------------------- 入口
    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler 的命名约定
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == "/api/health":
            self._json(self.app.health())
        elif path == "/api/examples":
            self._json({"items": self.app.examples()})
        elif path == "/api/history":
            self._json({"items": list_reports()})
        elif path == "/api/report":
            self._handle_report(parsed)
        elif path == "/api/run":
            self._handle_run(parsed)
        elif path == "/api/events":
            self._handle_events(parsed)
        elif path == "/api/memory":
            self._json({"items": self.app.memory_items()})
        elif path == "/api/concepts":
            self._json({"concepts": CONCEPTS})
        elif path in {"/", "/index.html"}:
            self._static("index.html")
        elif path.startswith("/static/"):
            self._static(path[len("/static/") :])
        elif path == "/favicon.ico":
            self._static("favicon.svg")
        else:
            self._json({"error": "页面不存在"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/analyze":
            self._handle_analyze()
        elif parsed.path == "/api/hitl":
            self._handle_hitl()
        elif parsed.path == "/api/chat":
            self._handle_chat()
        else:
            self._json({"error": "接口不存在"}, HTTPStatus.NOT_FOUND)

    # ------------------------------------------------------------- 属性
    @property
    def app(self) -> RepoLensApp:
        return self.server.app  # type: ignore[attr-defined]

    # ------------------------------------------------------------- 工具
    def log_message(self, fmt: str, *args: Any) -> None:
        # 默认日志太长，这里只保留方法 + 路径 + 状态码。
        print(f"[RepoLens] {self.address_string()} {fmt % args}")

    def _read_json(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        if length > 1_000_000:
            self._json({"error": "请求体太大"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return None
        try:
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json({"error": "请求体不是合法的 JSON"}, HTTPStatus.BAD_REQUEST)
            return None

    def _json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _static(self, relative: str) -> None:
        relative = unquote(relative)
        if relative.startswith("/"):
            relative = relative[1:]
        # 防目录穿越：把路径解析后确认仍在 static 目录内。
        try:
            target = (STATIC_DIR / relative).resolve()
            target.relative_to(STATIC_DIR.resolve())
        except (OSError, ValueError):
            self._json({"error": "非法路径"}, HTTPStatus.FORBIDDEN)
            return
        if not target.is_file():
            self._json({"error": "文件不存在"}, HTTPStatus.NOT_FOUND)
            return
        content_type = _content_type(target)
        try:
            body = target.read_bytes()
        except OSError:
            self._json({"error": "读取文件失败"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self' data:; connect-src 'self'",
        )
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    # ------------------------------------------------------------- 报告
    def _handle_report(self, parsed) -> None:
        query = parse_qs(parsed.query)
        run_id = (query.get("run_id") or [""])[0].strip()
        if not run_id:
            self._json({"error": "缺少 run_id"}, HTTPStatus.BAD_REQUEST)
            return
        report = self.app.get_report(run_id)
        if report is None:
            self._json({"error": "报告不存在或还没生成"}, HTTPStatus.NOT_FOUND)
            return
        self._json(report)

    def _handle_run(self, parsed) -> None:
        """刷新页面后，用 run_id 恢复进度或直接打开报告。"""
        query = parse_qs(parsed.query)
        run_id = (query.get("run_id") or [""])[0].strip()
        if not run_id:
            self._json({"error": "缺少 run_id"}, HTTPStatus.BAD_REQUEST)
            return
        run = self.app.get_run(run_id)
        if run is None:
            report = load_report(run_id)
            if report is not None:
                self._json(
                    {
                        "run_id": run_id,
                        "source": report.get("source", ""),
                        "source_type": report.get("source_type", "local"),
                        "status": "done",
                        "report_ready": True,
                        "elapsed_seconds": 0,
                        "repo_name": report.get("repo_name", ""),
                    }
                )
                return
            self._json({"error": "找不到这次分析"}, HTTPStatus.NOT_FOUND)
            return
        self._json(
            {
                "run_id": run.run_id,
                "source": run.source,
                "source_type": run.source_type,
                "status": run.status,
                "report_ready": run.ctx.report is not None,
                "elapsed_seconds": round(time.time() - run.created_at, 1),
                "repo_name": run.ctx.snapshot.repo_name if run.ctx.snapshot else "",
                "error": run.ctx.error,
            }
        )

    # ------------------------------------------------------------- 分析
    def _handle_analyze(self) -> None:
        payload = self._read_json()
        if payload is None:
            return
        source = str(payload.get("source", "")).strip()
        try:
            run = self.app.start_run(source)
        except SourceError as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except TooManyRuns as exc:
            self._json({"error": str(exc)}, HTTPStatus.TOO_MANY_REQUESTS)
            return
        except Exception as exc:  # 例如路径里包含非法字符
            self._json({"error": f"无法处理这个来源：{exc}"}, HTTPStatus.BAD_REQUEST)
            return
        cfg = config.load_model_config()
        self._json(
            {
                "run_id": run.run_id,
                "source_type": run.source_type,
                "model": cfg.display_name,
                "ai_available": cfg.available,
            }
        )

    def _handle_hitl(self) -> None:
        payload = self._read_json()
        if payload is None:
            return
        run_id = str(payload.get("run_id", "")).strip()
        decision = str(payload.get("decision", "")).strip()
        if decision not in {"approve", "reject"}:
            self._json({"error": "decision 只能是 approve 或 reject"}, HTTPStatus.BAD_REQUEST)
            return
        run = self.app.get_run(run_id)
        if run is None:
            self._json({"error": "找不到这次分析"}, HTTPStatus.NOT_FOUND)
            return
        ok = run.ctx.submit_decision(
            {"type": decision, "message": str(payload.get("message", ""))[:200]}
        )
        if not ok:
            self._json({"error": "当前没有等待确认的操作"}, HTTPStatus.CONFLICT)
            return
        self._json({"ok": True})

    # ------------------------------------------------------------- SSE
    def _sse_start(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.close_connection = True

    def _sse_send(self, event: dict) -> None:
        payload = json.dumps(event, ensure_ascii=False)
        lines = [f"data: {line}" for line in payload.splitlines() or [""]]
        chunk = "\n".join(lines) + "\n\n"
        self.wfile.write(chunk.encode("utf-8"))
        self.wfile.flush()

    def _handle_events(self, parsed) -> None:
        query = parse_qs(parsed.query)
        run_id = (query.get("run_id") or [""])[0].strip()
        if not run_id:
            self._json({"error": "缺少 run_id"}, HTTPStatus.BAD_REQUEST)
            return
        run = self.app.get_run(run_id)
        if run is None:
            self._json({"error": "找不到这次分析"}, HTTPStatus.NOT_FOUND)
            return
        try:
            last_seq = int((query.get("from") or ["0"])[0])
        except ValueError:
            last_seq = 0

        self._sse_start()
        bus = run.ctx.bus
        try:
            # 先补发已经发生的事件（从 seq=0 开始），再持续等待新事件。
            while True:
                if last_seq <= 0:
                    events = bus.snapshot(0)
                else:
                    events = bus.snapshot(last_seq)
                if events:
                    for event in events:
                        self._sse_send(event)
                        last_seq = event["seq"] + 1
                    continue
                if bus.closed:
                    break
                bus.wait_for_new(last_seq, timeout=12)
                if not bus.snapshot(last_seq):
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    # ------------------------------------------------------------- 追问
    def _handle_chat(self) -> None:
        payload = self._read_json()
        if payload is None:
            return
        run_id = str(payload.get("run_id", "")).strip()
        message = str(payload.get("message", "")).strip()
        if not run_id:
            self._json({"error": "缺少 run_id"}, HTTPStatus.BAD_REQUEST)
            return
        if not message:
            self._json({"error": "问题不能为空"}, HTTPStatus.BAD_REQUEST)
            return
        if len(message) > 2000:
            self._json({"error": "问题太长（最多 2000 字）"}, HTTPStatus.BAD_REQUEST)
            return
        run = self.app.get_run(run_id)
        if run is None:
            report = load_report(run_id)
            if report is None:
                self._json({"error": "找不到这次分析"}, HTTPStatus.NOT_FOUND)
                return
            run = self.app.ensure_run_for_report(run_id, report)
        if run.ctx.report is None:
            report = self.app.get_report(run_id)
            if report is None:
                self._json({"error": "报告还没生成，无法追问"}, HTTPStatus.CONFLICT)
                return
            run.ctx.report = report

        self._sse_start()
        try:
            with run.chat_lock:
                if run.chat_agent is None:
                    from .agent import build_chat_agent

                    run.chat_agent = build_chat_agent(run.ctx)
                for item in stream_chat(run.ctx, message, run.chat_agent):
                    self._sse_send(
                        {
                            "seq": int(time.time() * 1000),
                            "type": item["type"],
                            "data": item.get("data", {}),
                        }
                    )
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        except Exception as exc:  # noqa: BLE001
            try:
                self._sse_send({"seq": 0, "type": "error", "data": {"message": str(exc)}})
            except OSError:
                pass


class RepoLensHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], app: RepoLensApp) -> None:
        self.app = app
        super().__init__(address, RepoLensHandler)


def create_server(host: str | None = None, port: int | None = None) -> RepoLensHTTPServer:
    """创建服务器；端口被占用时自动往后找 5 个端口。"""
    host = host or config.HOST
    port = port or config.PORT
    app = RepoLensApp()
    last_error: OSError | None = None
    for offset in range(6):
        try:
            return RepoLensHTTPServer((host, port + offset), app)
        except OSError as exc:
            last_error = exc
            continue
    raise RuntimeError(f"无法启动服务器（端口 {port} 附近都被占用）：{last_error}")


def _content_type(path: Path) -> str:
    mapping = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".svg": "image/svg+xml",
        ".json": "application/json; charset=utf-8",
        ".ico": "image/x-icon",
        ".png": "image/png",
        ".woff2": "font/woff2",
    }
    return mapping.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


# ============================================================================
# "知识点讲解"文案（网页右侧帮助面板）
# ============================================================================
CONCEPTS: list[dict] = [
    {
        "id": "agent",
        "title": "Agent 是什么",
        "chapter": "教程第 7 章",
        "summary": "一个会自己循环『思考 → 调工具 → 看结果 → 再思考』的大模型程序。",
        "detail": (
            "普通调用大模型是『一问一答』；Agent 则多了一个循环：模型可以先调用工具（读文件、"
            "搜索、执行命令），拿到结果后再决定下一步。本项目用 LangChain 1.x 的 "
            "create_agent(model=..., tools=..., system_prompt=...) 创建 Agent。"
            "它的核心循环由 LangGraph 驱动：模型节点和工具节点交替执行，直到模型不再要求调用工具。"
        ),
    },
    {
        "id": "tool",
        "title": "工具 Tool",
        "chapter": "教程第 5、7 章",
        "summary": "用 @tool 装饰的普通 Python 函数，是 Agent 的『手和眼』。",
        "detail": (
            "大模型不能直接读你的硬盘。我们用 @tool(parse_docstring=True) 把函数暴露给模型，"
            "函数的 docstring 就是写给模型看的说明书（参数是什么意思、什么时候用）。"
            "本项目有 6 个工具：扫描本地仓库、克隆 GitHub、列出技术、核实技术、读文件、写长期记忆。"
            "模型根据 docstring 自己决定调用哪个、传什么参数。"
        ),
    },
    {
        "id": "structured",
        "title": "结构化输出",
        "chapter": "教程第 6、7 章",
        "summary": "让模型按 Pydantic 模型填表，而不是返回一段自由文本。",
        "detail": (
            "网页需要稳定的字段（name、category、role、modules），不能靠解析中文作文。"
            "create_agent(response_format=ToolStrategy(RepoInsight)) 会让模型调用一个隐藏的『提交』工具，"
            "参数必须符合 RepoInsight 的字段定义。填错时 handle_errors 会把中文纠错提示返回给模型，"
            "让它重填，而不是直接让整个任务失败。"
        ),
    },
    {
        "id": "middleware",
        "title": "中间件 Middleware",
        "chapter": "教程第 8 章",
        "summary": "挂在 Agent 流程节点上的钩子，用来做进度、审批、脱敏、限流、摘要。",
        "detail": (
            "例如 before_model 在模型思考前触发，wrap_tool_call 包住一次工具调用。"
            "本项目用了 6 个内置中间件：TodoListMiddleware（任务清单）、HumanInTheLoopMiddleware"
            "（克隆前要你批准）、ModelCallLimitMiddleware / ToolCallLimitMiddleware（防止无限循环）、"
            "ToolRetryMiddleware（工具失败重试）、PIIMiddleware（隐私信息打码）；"
            "另外自己写了 ProgressMiddleware（实时进度）和 SecretMaskingMiddleware（密钥脱敏）。"
        ),
    },
    {
        "id": "stream",
        "title": "流式输出 Streaming",
        "chapter": "教程第 7 章",
        "summary": "Agent 每走一步就推一条事件，而不是等几分钟后一次性返回。",
        "detail": (
            "agent.stream(..., stream_mode=['updates', 'custom']) 会持续产出事件："
            "updates 告诉你哪个节点更新了什么，custom 是工具内部用 get_stream_writer() 主动发出的进度。"
            "服务器把这些事件通过 SSE（Server-Sent Events）转发给浏览器，网页就能实时显示"
            "『正在扫描 300 个文件』『正在核实 FastAPI』。追问功能则使用 messages 模式做逐字输出。"
        ),
    },
    {
        "id": "memory",
        "title": "短期记忆与长期记忆",
        "chapter": "教程第 9 章",
        "summary": "Checkpointer 记住同一次对话；Store 跨会话保存结论。",
        "detail": (
            "短期记忆：create_agent(checkpointer=InMemorySaver()) + thread_id。"
            "同一个 thread_id 的多轮对话会带上历史，所以追问能记得你刚才问了什么。"
            "长期记忆：create_agent(store=InMemoryStore()) + 工具里的 runtime.store.put()。"
            "本项目在分析结束时把结论写入 ('repolens', 'analyses')，即使换一个会话也能读出来。"
            "生产环境可以把这两个组件换成 PostgreSQL/Redis 版本，接口不变。"
        ),
    },
    {
        "id": "hitl",
        "title": "Human-in-the-loop",
        "chapter": "教程第 8 章",
        "summary": "让 Agent 在『有副作用』的操作前停下来，等人类点批准。",
        "detail": (
            "克隆 GitHub 仓库会联网、写磁盘，所以本项目用 HumanInTheLoopMiddleware 拦截 "
            "clone_github_repository。Agent 会真的暂停（不是假装暂停），网页弹出确认框；"
            "你点同意后，服务器用 Command(resume={'decisions': [{'type': 'approve'}]}) 让 Agent 继续。"
            "如果拒绝，Agent 会收到拒绝结果，不会执行克隆。"
        ),
    },
    {
        "id": "facts",
        "title": "为什么还要写扫描器",
        "chapter": "工程实践",
        "summary": "让工具负责精确事实，让模型负责解释，避免『一本正经地胡说』。",
        "detail": (
            "大模型读不完几千个文件，也可能看漏。scanner.py 用纯 Python 精确统计文件、"
            "解析 requirements.txt / package.json / pom.xml 等依赖清单、提取 import 语句，"
            "得到『哪一行、哪个文件用了哪个技术』的硬证据。"
            "Agent 只在这些事实上做归纳和解释；两者合并后，报告既有可核对的证据，也有易懂的中文说明。"
        ),
    },
    {
        "id": "fallback",
        "title": "降级与安全",
        "chapter": "工程实践",
        "summary": "没有 API Key、模型超时、路径写错时，页面依然给出明确结果。",
        "detail": (
            "如果模型不可用，系统会跳过 AI 解读，只用扫描器生成报告，并在页面上标注"
            "『本次没有使用 AI 解读』。如果 Agent 忘了调用扫描工具，后台会兜底扫描一次。"
            "读取文件时会拒绝 .env、私钥，并对 api_key / password 等做脱敏；"
            "服务器默认只监听 127.0.0.1，不会暴露到局域网。"
        ),
    },
]
