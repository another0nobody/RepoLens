"""Watch 模式：检查本地仓库在报告生成后是否又发生了变化。"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

from .scanner import IGNORE_DIRS

MAX_WATCH_FILES = 3000


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def repo_status(report: dict) -> dict:
    """只读检查本地仓库；不读取文件内容，不修改任何东西。"""
    if str(report.get("source_type") or "") != "local":
        return {
            "available": False,
            "changed": False,
            "reason": "Watch 模式只用于本地目录",
        }

    raw_root = str(report.get("local_path") or "")
    root = Path(raw_root)
    if not raw_root or not root.is_dir():
        return {
            "available": False,
            "changed": False,
            "reason": "本地仓库目录不可用",
        }

    generated_at = str(report.get("generated_at") or "")
    try:
        baseline = datetime.fromisoformat(generated_at).timestamp()
    except (TypeError, ValueError):
        baseline = 0.0

    latest_mtime = 0.0
    latest_path = ""
    checked = 0
    truncated = False
    try:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
            dirnames[:] = sorted(
                name
                for name in dirnames
                if name.lower() not in IGNORE_DIRS and not name.lower().startswith(".git")
            )
            for filename in filenames:
                if checked >= MAX_WATCH_FILES:
                    truncated = True
                    break
                full_path = Path(dirpath) / filename
                try:
                    stat = full_path.stat()
                except OSError:
                    continue
                checked += 1
                if stat.st_mtime > latest_mtime:
                    latest_mtime = stat.st_mtime
                    latest_path = _relative(full_path, root)
            if truncated:
                break
    except OSError as exc:
        return {
            "available": False,
            "changed": False,
            "reason": f"读取目录失败：{exc}",
        }

    return {
        "available": True,
        "changed": bool(baseline and latest_mtime > baseline + 1.0),
        "baseline": baseline,
        "latest_mtime": latest_mtime,
        "latest_path": latest_path,
        "files_checked": checked,
        "truncated": truncated,
        "checked_at": time.time(),
    }
