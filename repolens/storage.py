"""SQLite 持久化：把运行、事件、追问消息和报告索引保存到本地。

为什么用 SQLite？
    - Python 标准库自带，不需要额外服务；
    - 单文件数据库，方便备份和排查；
    - 比“只放在内存里”可靠，刷新/重启后还能继续追问。

这里不替代报告 JSON：报告仍以 JSON 文件为主要可读格式，
SQLite 负责索引、事件回放和聊天记录。
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

DB_SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    repo_name TEXT NOT NULL DEFAULT '',
    local_path TEXT NOT NULL DEFAULT '',
    report_ready INTEGER NOT NULL DEFAULT 0,
    error TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);

CREATE TABLE IF NOT EXISTS events (
    run_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    type TEXT NOT NULL,
    data TEXT NOT NULL,
    ts REAL NOT NULL,
    PRIMARY KEY (run_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_events_run_seq ON events(run_id, seq);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL,
    meta TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_messages_run ON messages(run_id, id);

CREATE TABLE IF NOT EXISTS reports (
    run_id TEXT PRIMARY KEY,
    schema_version INTEGER NOT NULL,
    repo_name TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT '',
    generated_at TEXT NOT NULL DEFAULT '',
    tech_count INTEGER NOT NULL DEFAULT 0,
    code_files INTEGER NOT NULL DEFAULT 0,
    total_loc INTEGER NOT NULL DEFAULT 0,
    ai_used INTEGER NOT NULL DEFAULT 0,
    report_json TEXT NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reports_generated ON reports(generated_at DESC);
"""


def _json_default(value: Any) -> str:
    return str(value)


class SQLiteStore:
    """轻量的本地持久化层；数据库不可用时自动降级为空操作。"""

    def __init__(self, db_path: Path | str) -> None:
        self.path = Path(db_path)
        self.lock = threading.Lock()
        self.available = False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._init_schema()
            self.available = True
        except (OSError, sqlite3.Error):
            # 本地环境没有写权限时，应用仍应能运行；报告 JSON 是兜底。
            self.available = False

    # ------------------------------------------------------------------ 基础
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(_SCHEMA)
            current = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if current < DB_SCHEMA_VERSION:
                conn.execute(f"PRAGMA user_version = {DB_SCHEMA_VERSION}")
            conn.commit()
        finally:
            conn.close()

    def _write(self, sql: str, params: tuple[Any, ...] = ()) -> bool:
        if not self.available:
            return False
        with self.lock:
            conn = None
            try:
                conn = self._connect()
                conn.execute(sql, params)
                conn.commit()
                return True
            except sqlite3.Error:
                if conn is not None:
                    conn.rollback()
                return False
            finally:
                if conn is not None:
                    conn.close()

    def _read(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        if not self.available:
            return []
        conn = None
        try:
            conn = self._connect()
            return conn.execute(sql, params).fetchall()
        except sqlite3.Error:
            return []
        finally:
            if conn is not None:
                conn.close()

    # ------------------------------------------------------------------ 运行
    def upsert_run(
        self,
        run_id: str,
        source: str,
        source_type: str,
        status: str = "running",
        created_at: float | None = None,
        repo_name: str = "",
        local_path: str = "",
        report_ready: bool = False,
        error: str = "",
        model: str = "",
    ) -> bool:
        now = time.time()
        created = created_at or now
        return self._write(
            """
            INSERT INTO runs (
                run_id, source, source_type, status, created_at, updated_at,
                repo_name, local_path, report_ready, error, model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                status = excluded.status,
                updated_at = excluded.updated_at,
                repo_name = excluded.repo_name,
                local_path = excluded.local_path,
                report_ready = excluded.report_ready,
                error = excluded.error,
                model = excluded.model
            """,
            (
                run_id,
                source,
                source_type,
                status,
                created,
                now,
                repo_name,
                local_path,
                1 if report_ready else 0,
                error,
                model,
            ),
        )

    def update_run(self, run_id: str, **fields: Any) -> bool:
        allowed = {
            "status",
            "repo_name",
            "local_path",
            "report_ready",
            "error",
            "model",
        }
        values = {key: value for key, value in fields.items() if key in allowed}
        if not values:
            return False
        assignments = ", ".join(f"{key} = ?" for key in values)
        params = tuple(
            (1 if value is True else 0 if value is False else value)
            for value in values.values()
        )
        return self._write(
            f"UPDATE runs SET {assignments}, updated_at = ? WHERE run_id = ?",
            (*params, time.time(), run_id),
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        rows = self._read("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        return dict(rows[0]) if rows else None

    def list_runs(self, limit: int = 40) -> list[dict[str, Any]]:
        rows = self._read(
            "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?",
            (max(1, min(int(limit), 200)),),
        )
        return [dict(row) for row in rows]

    def mark_stale_runs(self) -> None:
        """进程重启后，把上次没跑完的运行标成中断，避免永远显示 running。"""
        self._write(
            "UPDATE runs SET status = 'error', error = ?, updated_at = ? WHERE status = 'running'",
            ("服务重启，运行已中断", time.time()),
        )

    # ------------------------------------------------------------------ 事件
    def append_event(self, run_id: str, event: dict[str, Any], max_events: int = 4000) -> bool:
        seq = int(event.get("seq", 0))
        payload = json.dumps(event.get("data", {}), ensure_ascii=False, default=_json_default)
        ok = self._write(
            "INSERT OR REPLACE INTO events (run_id, seq, type, data, ts) VALUES (?, ?, ?, ?, ?)",
            (
                run_id,
                seq,
                str(event.get("type", "")),
                payload,
                float(event.get("ts") or time.time()),
            ),
        )
        if ok:
            # 控制单次运行的事件量，避免数据库无限增长。
            self._write(
                """
                DELETE FROM events
                WHERE run_id = ? AND seq <= (
                    SELECT seq FROM events WHERE run_id = ?
                    ORDER BY seq DESC LIMIT 1 OFFSET ?
                )
                """,
                (run_id, run_id, max_events),
            )
        return ok

    def events(self, run_id: str, from_seq: int = 0, limit: int = 4000) -> list[dict[str, Any]]:
        rows = self._read(
            """
            SELECT seq, type, data, ts FROM events
            WHERE run_id = ? AND seq >= ?
            ORDER BY seq ASC LIMIT ?
            """,
            (run_id, max(0, int(from_seq)), max(1, min(int(limit), 4000))),
        )
        result: list[dict[str, Any]] = []
        for row in rows:
            try:
                data = json.loads(row["data"])
            except (TypeError, json.JSONDecodeError):
                data = {}
            result.append(
                {
                    "seq": int(row["seq"]),
                    "type": row["type"],
                    "data": data,
                    "ts": float(row["ts"]),
                }
            )
        return result

    # ------------------------------------------------------------------ 聊天
    def add_message(
        self,
        run_id: str,
        role: str,
        content: str,
        meta: dict[str, Any] | None = None,
    ) -> bool:
        return self._write(
            "INSERT INTO messages (run_id, role, content, created_at, meta) VALUES (?, ?, ?, ?, ?)",
            (
                run_id,
                role,
                content,
                time.time(),
                json.dumps(meta or {}, ensure_ascii=False, default=_json_default),
            ),
        )

    def messages(self, run_id: str, limit: int = 200) -> list[dict[str, Any]]:
        rows = self._read(
            "SELECT id, role, content, created_at, meta FROM messages WHERE run_id = ? ORDER BY id ASC LIMIT ?",
            (run_id, max(1, min(int(limit), 1000))),
        )
        result: list[dict[str, Any]] = []
        for row in rows:
            try:
                meta = json.loads(row["meta"])
            except (TypeError, json.JSONDecodeError):
                meta = {}
            result.append(
                {
                    "id": int(row["id"]),
                    "role": row["role"],
                    "content": row["content"],
                    "created_at": float(row["created_at"]),
                    "meta": meta,
                }
            )
        return result

    # ------------------------------------------------------------------ 报告
    def save_report(self, report: dict[str, Any]) -> bool:
        run_id = str(report.get("run_id") or "")
        if not run_id:
            return False
        stats = report.get("stats") or {}
        return self._write(
            """
            INSERT INTO reports (
                run_id, schema_version, repo_name, source, source_type, generated_at,
                tech_count, code_files, total_loc, ai_used, report_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                schema_version = excluded.schema_version,
                repo_name = excluded.repo_name,
                source = excluded.source,
                source_type = excluded.source_type,
                generated_at = excluded.generated_at,
                tech_count = excluded.tech_count,
                code_files = excluded.code_files,
                total_loc = excluded.total_loc,
                ai_used = excluded.ai_used,
                report_json = excluded.report_json,
                updated_at = excluded.updated_at
            """,
            (
                run_id,
                int(report.get("schema_version") or 1),
                str(report.get("repo_name") or ""),
                str(report.get("source") or ""),
                str(report.get("source_type") or ""),
                str(report.get("generated_at") or ""),
                len(report.get("techs") or []),
                int(stats.get("code_file_count") or 0),
                int(stats.get("total_loc") or 0),
                1 if (report.get("ai") or {}).get("used") else 0,
                json.dumps(report, ensure_ascii=False, default=_json_default),
                time.time(),
            ),
        )

    def load_report(self, run_id: str) -> dict[str, Any] | None:
        rows = self._read("SELECT report_json FROM reports WHERE run_id = ?", (run_id,))
        if not rows:
            return None
        try:
            data = json.loads(rows[0]["report_json"])
        except (TypeError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def list_reports(self, limit: int = 40) -> list[dict[str, Any]]:
        rows = self._read(
            """
            SELECT run_id, schema_version, repo_name, source, source_type, generated_at,
                   tech_count, code_files, total_loc, ai_used
            FROM reports ORDER BY generated_at DESC LIMIT ?
            """,
            (max(1, min(int(limit), 200)),),
        )
        return [
            {
                "run_id": row["run_id"],
                "schema_version": int(row["schema_version"]),
                "repo_name": row["repo_name"],
                "source": row["source"],
                "source_type": row["source_type"],
                "generated_at": row["generated_at"],
                "tech_count": int(row["tech_count"]),
                "code_files": int(row["code_files"]),
                "total_loc": int(row["total_loc"]),
                "ai_used": bool(row["ai_used"]),
            }
            for row in rows
        ]

    def stats(self) -> dict[str, int]:
        tables = ("runs", "events", "messages", "reports")
        result: dict[str, int] = {}
        for table in tables:
            rows = self._read(f"SELECT COUNT(*) AS count FROM {table}")
            result[table] = int(rows[0]["count"]) if rows else 0
        return result
