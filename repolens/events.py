"""事件总线：让"后台跑 Agent 的线程"和"浏览器"能够实时对话。

【给初学者：为什么需要它？】
Agent 分析一个仓库可能要几十秒，中间会调用很多工具。
如果等全部跑完再返回，网页就会一片空白，用户不知道程序是不是卡死了。

所以我们让 Agent 每走一步，就往一个"事件列表"里追加一条消息。
网页通过 SSE（Server-Sent Events，服务器推送）连上来看这个列表，
有新消息就立刻显示出来——这就是 ChatGPT 那种"打字机 / 进度条"效果的原理。

本文件只负责"存事件 + 通知新事件"，不懂 Agent，也不懂 HTTP，方便单独理解。
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any


class EventBus:
    """一个分析任务（run）对应一个 EventBus。

    线程安全：后台线程写、HTTP 线程读，用 Condition 做同步。
    on_event 可选：把事件同步写入 SQLite，进程重启后仍可回放。
    """

    def __init__(
        self,
        run_id: str,
        max_events: int = 4000,
        on_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.run_id = run_id
        self._events: list[dict[str, Any]] = []
        self._condition = threading.Condition()
        self._closed = False
        self._max_events = max_events
        self._next_seq = 0  # 单调递增，即使旧事件被裁剪也不会重复
        self._on_event = on_event

    # ------------------------------------------------------------------ 写
    def publish(self, event_type: str, data: Any = None) -> dict[str, Any]:
        """追加一条事件，并叫醒所有正在等待的读者。"""
        with self._condition:
            event = {
                "seq": self._next_seq,
                "type": event_type,
                "data": data if data is not None else {},
                "ts": time.time(),
            }
            self._next_seq += 1
            if len(self._events) >= self._max_events:
                # 事件太多时丢弃最老的，避免内存无限增长（正常分析不会触发）。
                keep_from = len(self._events) - self._max_events + 100
                del self._events[:keep_from]
            self._events.append(event)
            self._condition.notify_all()
        if self._on_event is not None:
            try:
                self._on_event(event)
            except Exception:
                # 持久化失败不能影响正在运行的分析。
                pass
        return event

    def close(self) -> None:
        """标记任务结束，让所有 SSE 连接可以正常退出。"""
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    # ------------------------------------------------------------------ 读
    def snapshot(self, from_seq: int = 0) -> list[dict[str, Any]]:
        """取出 from_seq 之后的所有事件（用于"补发"已经发生的历史）。"""
        with self._condition:
            if from_seq <= 0:
                return list(self._events)
            return [event for event in self._events if event["seq"] >= from_seq]

    def wait_for_new(self, from_seq: int, timeout: float = 15.0) -> list[dict[str, Any]]:
        """阻塞等待新事件；超时返回空列表（调用方可以借机发心跳）。"""
        with self._condition:
            if self._closed:
                return []
            self._condition.wait(timeout=timeout)
            if from_seq <= 0:
                return list(self._events)
            return [event for event in self._events if event["seq"] >= from_seq]

    @property
    def closed(self) -> bool:
        with self._condition:
            return self._closed
