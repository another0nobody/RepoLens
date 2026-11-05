"""回答 groundedness：检查回答里的文件/行号引用是否真的存在于报告中。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .codeview import CodeViewError, read_code_window

CITATION_RE = re.compile(
    r"(?<![\w/])((?:[A-Za-z0-9_.@-]+/)*[A-Za-z0-9_.@-]+\.(?:py|pyi|ts|tsx|js|jsx|vue|svelte|go|java|kt|rs|rb|php|cs|c|cc|cpp|h|hpp|md|json|ya?ml|toml|txt|sh|ps1))(?::(\d+))?"
)
MAX_TEXT = 20000


def _normalize_path(path: str) -> str:
    value = str(path or "").strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def _file_has_line(report: dict, path: str, line: int) -> bool:
    root = str(report.get("local_path") or "")
    if not root or not Path(root).is_dir():
        return False
    try:
        window = read_code_window(root, path, line=line, context=0)
        return int(window.get("line") or 0) == int(line)
    except CodeViewError:
        return False


def collect_known(report: dict) -> tuple[set[str], dict[str, set[int]]]:
    paths: set[str] = set()
    lines: dict[str, set[int]] = {}

    def add(path: str, line: Any = None) -> None:
        value = _normalize_path(path)
        if not value:
            return
        paths.add(value)
        if line is not None:
            try:
                number = int(line)
            except (TypeError, ValueError):
                return
            if number > 0:
                lines.setdefault(value, set()).add(number)

    for path in report.get("entry_points") or []:
        add(path)
    for node in (report.get("module_graph") or {}).get("nodes") or []:
        if isinstance(node, dict):
            add(node.get("path"))
    for tech in report.get("techs") or []:
        if not isinstance(tech, dict):
            continue
        for module in tech.get("modules") or []:
            if isinstance(module, dict):
                add(module.get("path"), module.get("line"))
        for evidence in tech.get("evidence") or []:
            if isinstance(evidence, dict):
                add(evidence.get("path"), evidence.get("line"))
        for path in tech.get("key_modules") or []:
            add(path)
    return paths, lines


def check_grounding(report: dict, text: str) -> dict:
    raw = str(text or "")[:MAX_TEXT]
    source = raw.replace("\\", "/")
    known_paths, known_lines = collect_known(report)

    found: dict[tuple[str, int | None], dict] = {}
    for match in CITATION_RE.finditer(source):
        path = _normalize_path(match.group(1))
        line = int(match.group(2)) if match.group(2) else None
        key = (path, line)
        if key in found:
            continue
        if path not in known_paths:
            status, reason = "invalid", "报告中没有这个文件"
        elif line is None:
            status, reason = "valid", "文件存在于报告中"
        elif path in known_lines and line in known_lines[path]:
            status, reason = "valid", "文件与行号都能在报告中核对"
        elif _file_has_line(report, path, line):
            status, reason = "valid", "文件行号在仓库中可核对"
        elif path not in known_lines:
            status, reason = "partial", "文件存在，但报告没有该文件的行号，且无法读取仓库"
        else:
            status, reason = "invalid", "文件存在，但行号不在报告证据中"
        found[key] = {
            "path": path,
            "line": line,
            "status": status,
            "reason": reason,
        }

    citations = list(found.values())
    total = len(citations)
    valid = sum(1 for item in citations if item["status"] == "valid")
    partial = sum(1 for item in citations if item["status"] == "partial")
    score = round(((valid + partial * 0.5) / total) * 100) if total else 0
    return {
        "has_citations": bool(citations),
        "score": score,
        "total": total,
        "valid": valid,
        "partial": partial,
        "invalid": total - valid - partial,
        "citations": citations,
    }
