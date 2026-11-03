"""风险面板：把报告里的风险、依赖结构和扫描限制整理成可筛选的发现。"""

from __future__ import annotations

import re
from typing import Any

MAX_FINDINGS = 30
SEVERITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}
SEVERITY_LABEL = {"high": "高", "medium": "中", "low": "低"}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _slug(text: str, index: int) -> str:
    cleaned = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", text.lower()).strip("-")
    return f"risk-{index}-{cleaned[:48] or 'finding'}"


def _risk_title(text: str) -> str:
    first = re.split(r"[。；;，,]", text, maxsplit=1)[0].strip()
    return (first or text)[:80]


def _severity_for_text(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("密码", "密钥", "secret", "password", "未使用版本", "安全", "敏感")):
        return "high"
    if any(word in lowered for word in ("缺少", "没有", "未", "风险", "截断", "不一致")):
        return "medium"
    return "low"


def _evidence_for_tech(tech: dict) -> list[dict]:
    evidence = []
    for item in (tech.get("evidence") or [])[:3]:
        if isinstance(item, dict) and item.get("path"):
            evidence.append(
                {
                    "path": item.get("path"),
                    "line": item.get("line", 1),
                    "label": item.get("kind") or "证据",
                }
            )
    return evidence


def _finding(
    findings: list[dict],
    severity: str,
    category: str,
    title: str,
    detail: str,
    action: str,
    evidence: list[dict] | None = None,
    tech: str = "",
) -> None:
    title = _text(title)
    if not title or any(item["title"] == title for item in findings):
        return
    findings.append(
        {
            "id": _slug(title, len(findings) + 1),
            "severity": severity,
            "severity_label": SEVERITY_LABEL[severity],
            "category": category,
            "title": title,
            "detail": _text(detail),
            "action": _text(action),
            "tech": tech,
            "evidence": (evidence or [])[:6],
        }
    )


def build_risk_panel(report: dict) -> dict:
    findings: list[dict] = []
    risks = [_text(item) for item in report.get("risks") or [] if _text(item)]

    for risk in risks:
        _finding(
            findings,
            _severity_for_text(risk),
            "报告风险",
            _risk_title(risk),
            risk,
            "确认风险范围；需要时打开相关技术或代码补充证据。",
        )

    graph = report.get("module_graph") or {}
    nodes = graph.get("nodes") or []
    cycle_nodes = [node.get("path") for node in nodes if isinstance(node, dict) and node.get("cycle")]
    cycle_count = int((graph.get("stats") or {}).get("cycle_count") or 0)
    if cycle_count or cycle_nodes:
        if not any("循环" in item["title"] for item in findings):
            _finding(
                findings,
                "medium",
                "依赖结构",
                f"发现 {cycle_count or len(cycle_nodes)} 个循环依赖回边",
                "模块依赖图中存在回边，可能增加理解、测试和拆分的成本。",
                "从回边所在文件开始拆分职责，或确认这是可接受的框架/包结构。",
                evidence=[{"path": path, "line": 1, "label": "循环模块"} for path in cycle_nodes[:5] if path],
            )

    test_techs = [tech for tech in report.get("techs") or [] if _text(tech.get("category")) == "测试与质量"]
    test_files = [
        node.get("path")
        for node in nodes
        if isinstance(node, dict) and re.search(r"(^|/)(test|tests|spec|__tests__)(/|$)", _text(node.get("path")))
    ]
    if not test_techs and not test_files and not any("测试" in item["title"] for item in findings):
        _finding(
            findings,
            "high",
            "质量保障",
            "没有发现测试证据",
            "报告没有识别到测试框架或测试文件；这不等于没有测试，但当前扫描没有可核对的证据。",
            "补充 pytest/vitest 等测试；或把已有测试放到扫描器能识别的路径。",
        )

    weak_techs = [
        tech
        for tech in report.get("techs") or []
        if _text(tech.get("category")) not in {"编程语言", "其他依赖"}
        and (_text(tech.get("confidence")) == "低" or bool(tech.get("ai_inferred")))
    ]
    if weak_techs:
        names = "、".join(_text(tech.get("name")) for tech in weak_techs[:6])
        _finding(
            findings,
            "low",
            "证据质量",
            f"{len(weak_techs)} 项技术置信度较低或来自 AI 推断",
            f"需要人工确认：{names}。",
            "打开技术详情核对证据；不要直接把推断当成生产依赖。",
            evidence=[item for tech in weak_techs[:3] for item in _evidence_for_tech(tech)],
        )

    if not any("CI" in item["title"] or "流水线" in item["title"] for item in findings):
        has_ci = any(
            _text(tech.get("name")) in {"GitHub Actions", "GitLab CI", "Jenkins", "CircleCI", "Travis CI"}
            for tech in report.get("techs") or []
        )
        if not has_ci:
            _finding(
                findings,
                "low",
                "工程流程",
                "没有发现 CI 流水线证据",
                "扫描没有识别到 GitHub Actions、GitLab CI 等持续集成配置。",
                "如果项目还没有 CI，可以先加最小 lint/test 工作流；如果已有，确认配置文件是否被扫描器识别。",
            )

    if (report.get("stats") or {}).get("truncated") or any("截断" in _text(item) for item in report.get("warnings") or []):
        _finding(
            findings,
            "medium",
            "扫描限制",
            "本次扫描被截断",
            "仓库文件或内容超过扫描上限，风险面板只覆盖已扫描部分。",
            "缩小分析目录范围，或先用更小的子目录确认关键风险。",
        )

    for warning in report.get("warnings") or []:
        text = _text(warning)
        if not text or len(findings) >= MAX_FINDINGS:
            continue
        if any(text[:30] in item["detail"] for item in findings):
            continue
        _finding(
            findings,
            _severity_for_text(text),
            "扫描提示",
            text[:90],
            text,
            "确认这是否会影响本次报告的完整性。",
        )

    counts = {
        "high": sum(1 for item in findings if item["severity"] == "high"),
        "medium": sum(1 for item in findings if item["severity"] == "medium"),
        "low": sum(1 for item in findings if item["severity"] == "low"),
    }
    score = min(100, counts["high"] * 28 + counts["medium"] * 10 + counts["low"] * 3)
    level = "high" if counts["high"] else "medium" if counts["medium"] else "low" if findings else "none"
    return {
        "level": level,
        "score": score,
        "counts": counts,
        "total": len(findings),
        "findings": findings[:MAX_FINDINGS],
    }
