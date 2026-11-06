"""语义 groundedness：让模型判断“这行代码是否支持回答里的结论”。

这是可选的深度核对，默认不自动运行；只有用户在回答下点击“深度核对”才调用模型。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import config
from .agent import build_model
from .codeview import CodeViewError, read_code_window
from .grounding import check_grounding

VERDICTS = {"support": "支持", "partial": "部分支持", "unsupported": "不支持"}
MAX_CLAIMS = 5


class SemanticError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def _sentence_around(text: str, path: str, line: int | None) -> str:
    marker = f"{path}:{line}" if line else path
    index = text.find(marker)
    if index < 0:
        index = text.find(path)
    if index < 0:
        return text[:300]
    start = max(0, index - 180)
    end = min(len(text), index + len(marker) + 220)
    snippet = text[start:end].strip()
    return snippet[:420]


def _code_for(report: dict, path: str, line: int) -> str:
    root = str(report.get("local_path") or "")
    if not root or not Path(root).is_dir():
        return ""
    try:
        window = read_code_window(root, path, line=line, context=2)
    except CodeViewError:
        return ""
    return "\n".join(f"{item['number']}: {item['text']}" for item in window.get("lines") or [])


def _prompt(answer: str, claims: list[dict]) -> str:
    blocks = []
    for index, claim in enumerate(claims):
        blocks.append(
            f"### 引用 {index}\n"
            f"位置：{claim['path']}:{claim['line']}\n"
            f"回答片段：{claim['sentence']}\n"
            f"代码：\n{claim['code'] or '（无法读取源码）'}\n"
        )
    return (
        "你是代码证据审阅器。对每个引用判断：给出的代码行是否支持回答片段里的结论。\n"
        "只能依据给出的代码和回答片段，不要使用外部知识；不确定时用 partial 或 unsupported。\n"
        "严格只返回 JSON，不要 Markdown 代码块：\n"
        '{"results":[{"index":0,"verdict":"support|partial|unsupported","reason":"不超过 50 字","quote":"代码中的关键行"}]}\n\n'
        f"完整回答（可能很长，只作为上下文）：\n{answer[:2500]}\n\n" + "\n".join(blocks)
    )


def _message_text(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content
        )
    return str(content or "")


def _parse_results(raw: str, count: int) -> list[dict]:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise SemanticError("模型没有返回可解析的核对结果", 502)
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise SemanticError("模型返回的核对结果不是合法 JSON", 502) from exc
    rows = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise SemanticError("模型返回的核对结果缺少 results", 502)
    by_index = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            index = int(row.get("index"))
        except (TypeError, ValueError):
            continue
        verdict = str(row.get("verdict") or "").strip().lower()
        if verdict not in VERDICTS:
            verdict = "partial"
        by_index[index] = {
            "verdict": verdict,
            "verdict_label": VERDICTS[verdict],
            "reason": str(row.get("reason") or "")[:200],
            "quote": str(row.get("quote") or "")[:240],
        }
    results = []
    for index in range(count):
        item = by_index.get(index) or {
            "verdict": "partial",
            "verdict_label": VERDICTS["partial"],
            "reason": "模型没有单独判断这一条",
            "quote": "",
        }
        results.append(item)
    return results


def review(report: dict, text: str, model: Any = None) -> dict:
    answer = str(text or "").strip()
    if not answer:
        raise SemanticError("回答内容不能为空", 400)
    grounding = check_grounding(report, answer)
    citations = [
        item
        for item in grounding.get("citations") or []
        if item.get("status") != "invalid" and item.get("line")
    ][:MAX_CLAIMS]
    if not citations:
        raise SemanticError("回答没有可核对的文件/行号引用", 400)

    if model is None:
        cfg = config.load_model_config()
        if not cfg.available:
            raise SemanticError("没有配置模型，无法做深度核对", 503)
        model = build_model(cfg)

    claims = []
    for item in citations:
        claims.append(
            {
                "path": item["path"],
                "line": int(item["line"]),
                "sentence": _sentence_around(answer, item["path"], item.get("line")),
                "code": _code_for(report, item["path"], int(item["line"])),
            }
        )
    response = model.invoke(_prompt(answer, claims))
    results = _parse_results(_message_text(response), len(claims))
    for claim, result in zip(claims, results):
        result["path"] = claim["path"]
        result["line"] = claim["line"]
    score = round(
        sum(1.0 if item["verdict"] == "support" else 0.5 if item["verdict"] == "partial" else 0.0 for item in results)
        / len(results)
        * 100
    )
    return {
        "score": score,
        "total": len(results),
        "results": results,
        "truncated": len(grounding.get("citations") or []) > MAX_CLAIMS,
    }
