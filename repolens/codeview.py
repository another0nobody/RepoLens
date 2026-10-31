"""只读代码片段：给网页的证据查看器提供安全的一小段源码。"""

from __future__ import annotations

from pathlib import Path

from .scanner import LANGUAGE_BY_SUFFIX
from .security import is_sensitive_path, mask_secrets

MAX_FILE_BYTES = 400_000
MAX_LINE_CHARS = 500
MAX_CONTEXT = 20


class CodeViewError(Exception):
    """代码读取失败；status 供 HTTP 层使用。"""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def read_code_window(
    repo_root: Path | str,
    relative_path: str,
    line: int = 1,
    context: int = 8,
) -> dict:
    """读取仓库内文件的一段，返回带行号的窗口。

    安全边界：
        - 路径必须解析到 repo_root 内；
        - 拒绝 .env、私钥等敏感文件；
        - 拒绝二进制/超大文件；
        - 返回内容做密钥脱敏。
    """
    relative_path = (relative_path or "").replace("\\", "/").strip().lstrip("/")
    if not relative_path:
        raise CodeViewError("缺少文件路径", 400)
    parts = Path(relative_path).parts
    if ".." in parts:
        raise CodeViewError("只允许读取仓库内的文件", 403)
    if any(part.lower() in {".git", ".ssh", ".aws", ".gnupg"} for part in parts):
        raise CodeViewError("出于安全考虑，不能读取版本库或密钥目录", 403)
    if is_sensitive_path(relative_path):
        raise CodeViewError("出于安全考虑，不能读取 .env、私钥等敏感文件", 403)

    root = Path(repo_root).resolve()
    target = (root / relative_path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise CodeViewError("只允许读取仓库内的文件", 403) from exc
    if not target.is_file():
        raise CodeViewError("文件不存在", 404)
    try:
        if target.stat().st_size > MAX_FILE_BYTES:
            raise CodeViewError("文件太大，无法在查看器中打开", 413)
        raw = target.read_bytes()
    except OSError as exc:
        raise CodeViewError(f"读取文件失败：{exc}", 500) from exc
    if b"\x00" in raw[:4096]:
        raise CodeViewError("这是二进制文件，不能按文本查看", 415)

    text = raw.decode("utf-8", errors="replace")
    text, hits = mask_secrets(text)
    lines = text.splitlines()
    if not lines:
        lines = [""]

    try:
        wanted = int(line or 1)
    except (TypeError, ValueError):
        wanted = 1
    wanted = max(1, min(wanted, len(lines)))
    try:
        span = int(context or 8)
    except (TypeError, ValueError):
        span = 8
    span = max(1, min(span, MAX_CONTEXT))
    start = max(1, wanted - span)
    end = min(len(lines), wanted + span)
    language_info = LANGUAGE_BY_SUFFIX.get(target.suffix.lower())
    language = language_info[0] if language_info else ""

    window = [
        {
            "number": number,
            "text": lines[number - 1][:MAX_LINE_CHARS],
            "highlight": number == wanted,
        }
        for number in range(start, end + 1)
    ]
    return {
        "path": relative_path,
        "line": wanted,
        "start": start,
        "end": end,
        "language": language,
        "lines": window,
        "masked": hits > 0,
        "truncated": start > 1 or end < len(lines),
        "total_lines": len(lines),
    }
