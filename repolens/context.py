"""一次分析的"共享上下文"。

【给初学者：这是什么？】
Agent 的工具（Tool）是普通的 Python 函数，但它们需要知道：
    - 这次分析是哪个 run？
    - 仓库扫描结果放在哪？
    - 网页上要显示什么进度？
    - 用户有没有批准克隆？

把这些东西打包成一个 AnalysisContext 对象，工具通过"闭包"拿到它。
这比用全局变量安全，也更容易理解：一次分析 = 一个 ctx。
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .events import EventBus
from .scanner import Snapshot


@dataclass
class AnalysisContext:
    """一次分析任务的全部共享状态。"""

    run_id: str
    source: str
    source_type: str  # "local" 或 "github"
    bus: EventBus
    store: Any = None
    checkpointer: Any = None
    model_display: str = ""

    # 仓库
    repo_root: Path | None = None
    snapshot: Snapshot | None = None
    source_note: str = ""

    # 结果
    report: dict | None = None
    error: str | None = None

    # 人机协同（Human-in-the-loop）用：用户批准/拒绝工具调用
    decision_event: threading.Event = field(default_factory=threading.Event)
    decision: dict | None = None
    interrupt_payload: dict | None = None

    cancelled: bool = False
    started_at: float = field(default_factory=time.time)
    token_usage: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0})

    # ------------------------------------------------------------------ 事件
    def emit(self, event_type: str, data: Any = None) -> None:
        """往事件总线写一条事件（网页会实时收到）。"""
        self.bus.publish(event_type, data if data is not None else {})

    def log(self, message: str, level: str = "info") -> None:
        self.emit("log", {"message": message, "level": level})

    def progress(self, message: str, **extra: Any) -> None:
        """报告扫描进度。

        优先使用 LangGraph 的 custom stream（教程里的 stream_mode="custom"）：
        工具内部调用 get_stream_writer() 发消息，由 agent.stream 实时转发。
        如果当前不在图里（例如单元测试直接调用工具），退回事件总线。
        """
        payload = {"message": message, **extra}
        try:
            from langgraph.config import get_stream_writer

            writer = get_stream_writer()
            writer({"type": "progress", **payload})
            return
        except Exception:
            pass
        self.emit("progress", payload)

    def finish(self) -> None:
        self.bus.close()

    # ------------------------------------------------------ 人机协同决策
    def wait_for_decision(self, timeout: float = 300.0) -> dict | None:
        """等待网页上的"批准/拒绝"；超时返回 None。"""
        self.decision_event.clear()
        self.decision = None
        self.decision_event.wait(timeout=timeout)
        return self.decision

    def submit_decision(self, decision: dict) -> bool:
        """由 HTTP 线程调用：用户点了批准/拒绝。"""
        if self.interrupt_payload is None:
            return False
        self.decision = decision
        self.decision_event.set()
        return True
