"""确定性的多仓库评测 Harness。

只跑扫描器，不调用模型：用可解释的事实指标衡量改动的收益与回归。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from repolens.scanner import Snapshot, scan_repository


def normalize(name: str) -> str:
    return str(name or "").strip().lower()


def evaluate_snapshot(snapshot: Snapshot, case: dict) -> dict:
    expected = case.get("expected") or {}
    expected_techs = expected.get("techs") or []
    expected_languages = expected.get("languages") or []
    expected_entries = expected.get("entry_points") or []

    detected_techs = {normalize(tech.name): tech.name for tech in snapshot.techs}
    matched_techs = [name for name in expected_techs if normalize(name) in detected_techs]
    missing_techs = [name for name in expected_techs if normalize(name) not in detected_techs]
    extra_techs = sorted(
        name for key, name in detected_techs.items() if key not in {normalize(item) for item in expected_techs}
    )

    detected_langs = {normalize(item.get("name")) for item in snapshot.languages if item.get("is_code")}
    missing_languages = [name for name in expected_languages if normalize(name) not in detected_langs]

    entry_set = {normalize(item) for item in snapshot.entry_points}
    missing_entries = [path for path in expected_entries if normalize(path) not in entry_set]

    graph = snapshot.module_graph or {}
    graph_nodes = len(graph.get("nodes") or [])
    graph_edges = len(graph.get("edges") or [])
    evidence_ratio = (
        round(
            sum(1 for tech in snapshot.techs if tech.evidence or tech.modules) / max(1, len(snapshot.techs)),
            3,
        )
        if snapshot.techs
        else 0.0
    )

    tech_recall = round(len(matched_techs) / max(1, len(expected_techs)), 3)
    tech_precision = round(len(matched_techs) / max(1, len(detected_techs)), 3)
    checks = {
        "techs": not missing_techs,
        "languages": not missing_languages,
        "entry_points": not missing_entries,
        "files": snapshot.file_count >= int(expected.get("min_files", 0)),
        "loc": snapshot.total_loc >= int(expected.get("min_loc", 0)),
        "graph_nodes": graph_nodes >= int(expected.get("min_graph_nodes", 0)),
        "graph_edges": graph_edges >= int(expected.get("min_graph_edges", 0)),
        "evidence_ratio": evidence_ratio >= float(expected.get("min_evidence_ratio", 0.0)),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "metrics": {
            "tech_recall": tech_recall,
            "tech_precision": tech_precision,
            "evidence_ratio": evidence_ratio,
            "file_count": snapshot.file_count,
            "code_file_count": snapshot.code_file_count,
            "total_loc": snapshot.total_loc,
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges,
            "truncated": snapshot.truncated,
        },
        "matched_techs": matched_techs,
        "missing_techs": missing_techs,
        "extra_techs": extra_techs,
        "missing_languages": missing_languages,
        "missing_entry_points": missing_entries,
    }


def run_cases(cases: list[dict], base_dir: Path) -> dict:
    results = []
    for case in cases:
        case_id = str(case.get("id") or "case")
        root = (base_dir / str(case.get("path") or "")).resolve()
        if not root.is_dir():
            results.append(
                {
                    "id": case_id,
                    "path": str(case.get("path")),
                    "passed": False,
                    "error": "目录不存在",
                    "metrics": {},
                    "checks": {},
                }
            )
            continue
        try:
            snapshot = scan_repository(root, str(case.get("path")), "eval")
            result = evaluate_snapshot(snapshot, case)
            result.update({"id": case_id, "path": str(case.get("path")), "error": ""})
            results.append(result)
        except Exception as exc:  # 评测隔离：一个用例失败不阻止其他仓库。
            results.append(
                {
                    "id": case_id,
                    "path": str(case.get("path")),
                    "passed": False,
                    "error": str(exc),
                    "metrics": {},
                    "checks": {},
                }
            )

    passed = sum(1 for item in results if item.get("passed"))
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
        },
        "cases": results,
    }


def render_markdown(result: dict) -> str:
    summary = result.get("summary") or {}
    lines = [
        "# RepoLens 评测报告",
        "",
        f"- 生成时间：{result.get('generated_at', '')}",
        f"- 用例：{summary.get('total', 0)}，通过：{summary.get('passed', 0)}，失败：{summary.get('failed', 0)}",
        "",
        "| 用例 | 结果 | 技术召回 | 证据覆盖 | 文件数 | LOC | 图节点/边 | 缺失 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in result.get("cases") or []:
        metrics = item.get("metrics") or {}
        missing = "、".join((item.get("missing_techs") or []) + (item.get("missing_languages") or []))
        if item.get("missing_entry_points"):
            missing = f"{missing}、入口 {', '.join(item['missing_entry_points'])}".strip("、")
        lines.append(
            "| {id} | {status} | {recall} | {evidence} | {files} | {loc} | {nodes}/{edges} | {missing} |".format(
                id=item.get("id", ""),
                status="通过" if item.get("passed") else "失败",
                recall=metrics.get("tech_recall", "—"),
                evidence=metrics.get("evidence_ratio", "—"),
                files=metrics.get("file_count", "—"),
                loc=metrics.get("total_loc", "—"),
                nodes=metrics.get("graph_nodes", "—"),
                edges=metrics.get("graph_edges", "—"),
                missing=missing or (item.get("error") or "—"),
            )
        )
    lines.extend(
        [
            "",
            "> 评测只检查扫描事实，不调用模型；extra_techs 是词典识别出的额外技术，不直接算失败。",
            "",
        ]
    )
    return "\n".join(lines)


def load_cases(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = raw.get("cases") if isinstance(raw, dict) else raw
    if not isinstance(cases, list):
        raise ValueError("cases.json 必须是数组或带 cases 数组的对象")
    return cases
