"""报告 Diff：比较两份分析结果，回答“这次和上次有什么变化”。"""

from __future__ import annotations

from typing import Any

MAX_DIFF_ITEMS = 40


def _text(value: Any) -> str:
    return str(value or "").strip()


def _cap(items: list[dict]) -> list[dict]:
    return items[:MAX_DIFF_ITEMS]


def _tech_key(tech: dict) -> str:
    return _text(tech.get("key")) or _text(tech.get("name")).lower()


def _tech_label(tech: dict) -> str:
    return _text(tech.get("name")) or _tech_key(tech)


def _tech_summary(tech: dict) -> dict:
    return {
        "name": _tech_label(tech),
        "category": _text(tech.get("category")),
        "layer": _text(tech.get("layer")),
        "function": _text(tech.get("function")),
        "version": _text(tech.get("version")),
        "confidence": _text(tech.get("confidence")),
        "module_count": int(tech.get("module_count") or len(tech.get("modules") or [])),
    }


def _text_list_diff(base: list, target: list, label: str) -> dict:
    base_items = [_text(item) for item in (base or []) if _text(item)]
    target_items = [_text(item) for item in (target or []) if _text(item)]
    base_set = set(base_items)
    target_set = set(target_items)
    added = [item for item in target_items if item not in base_set]
    removed = [item for item in base_items if item not in target_set]
    return {
        "label": label,
        "added": added[:MAX_DIFF_ITEMS],
        "removed": removed[:MAX_DIFF_ITEMS],
        "added_count": len(added),
        "removed_count": len(removed),
    }


def _tech_diff(base: dict, target: dict) -> dict:
    base_map = {_tech_key(tech): tech for tech in base.get("techs") or [] if isinstance(tech, dict)}
    target_map = {_tech_key(tech): tech for tech in target.get("techs") or [] if isinstance(tech, dict)}
    added = [_tech_summary(tech) for key, tech in target_map.items() if key not in base_map]
    removed = [_tech_summary(tech) for key, tech in base_map.items() if key not in target_map]

    field_labels = {
        "version": "版本",
        "category": "分类",
        "layer": "层级",
        "function": "功能",
        "confidence": "置信度",
        "module_count": "模块数",
        "evidence_count": "证据数",
        "source_count": "来源数",
        "usage_tags": "用途",
    }
    changed = []
    for key in sorted(set(base_map) & set(target_map)):
        old = base_map[key]
        new = target_map[key]
        old_values = {
            "version": _text(old.get("version")),
            "category": _text(old.get("category")),
            "layer": _text(old.get("layer")),
            "function": _text(old.get("function")),
            "confidence": _text(old.get("confidence")),
            "module_count": int(old.get("module_count") or len(old.get("modules") or [])),
            "evidence_count": len(old.get("evidence") or []),
            "source_count": len(old.get("sources") or []),
            "usage_tags": "、".join(sorted(old.get("usage_tags") or [])),
        }
        new_values = {
            "version": _text(new.get("version")),
            "category": _text(new.get("category")),
            "layer": _text(new.get("layer")),
            "function": _text(new.get("function")),
            "confidence": _text(new.get("confidence")),
            "module_count": int(new.get("module_count") or len(new.get("modules") or [])),
            "evidence_count": len(new.get("evidence") or []),
            "source_count": len(new.get("sources") or []),
            "usage_tags": "、".join(sorted(new.get("usage_tags") or [])),
        }
        changes = [
            {
                "field": field,
                "label": field_labels[field],
                "base": old_values[field],
                "target": new_values[field],
            }
            for field in field_labels
            if old_values[field] != new_values[field]
        ]
        if changes:
            changed.append({**_tech_summary(new), "changes": changes})
    return {
        "added": _cap(added),
        "removed": _cap(removed),
        "changed": _cap(changed),
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
    }


def _module_diff(base: dict, target: dict) -> dict:
    old_graph = base.get("module_graph") or {}
    new_graph = target.get("module_graph") or {}
    old_nodes = {node.get("id"): node for node in old_graph.get("nodes") or [] if isinstance(node, dict)}
    new_nodes = {node.get("id"): node for node in new_graph.get("nodes") or [] if isinstance(node, dict)}
    old_edges = {
        (_text(edge.get("source")), _text(edge.get("target")))
        for edge in old_graph.get("edges") or []
        if isinstance(edge, dict)
    }
    new_edges = {
        (_text(edge.get("source")), _text(edge.get("target")))
        for edge in new_graph.get("edges") or []
        if isinstance(edge, dict)
    }
    nodes_added = [
        {"path": path, "dir": node.get("dir", ""), "loc": node.get("loc", 0)}
        for path, node in new_nodes.items()
        if path not in old_nodes
    ]
    nodes_removed = [
        {"path": path, "dir": node.get("dir", ""), "loc": node.get("loc", 0)}
        for path, node in old_nodes.items()
        if path not in new_nodes
    ]
    edges_added = [{"source": source, "target": target} for source, target in new_edges - old_edges if source and target]
    edges_removed = [{"source": source, "target": target} for source, target in old_edges - new_edges if source and target]
    return {
        "nodes_added": nodes_added[:MAX_DIFF_ITEMS],
        "nodes_removed": nodes_removed[:MAX_DIFF_ITEMS],
        "edges_added": edges_added[:MAX_DIFF_ITEMS],
        "edges_removed": edges_removed[:MAX_DIFF_ITEMS],
        "nodes_added_count": len(nodes_added),
        "nodes_removed_count": len(nodes_removed),
        "edges_added_count": len(edges_added),
        "edges_removed_count": len(edges_removed),
        "cycle_delta": int((new_graph.get("stats") or {}).get("cycle_count") or 0)
        - int((old_graph.get("stats") or {}).get("cycle_count") or 0),
    }


def build_diff(base: dict, target: dict) -> dict:
    """比较 base（旧）与 target（新）两份已规范化报告。"""
    techs = _tech_diff(base, target)
    modules = _module_diff(base, target)
    old_stats = base.get("stats") or {}
    new_stats = target.get("stats") or {}

    stat_specs = [
        ("file_count", "文件总数"),
        ("code_file_count", "代码文件"),
        ("total_loc", "代码行数"),
    ]
    stats = []
    for key, label in stat_specs:
        old = int(old_stats.get(key) or 0)
        new = int(new_stats.get(key) or 0)
        stats.append({"key": key, "label": label, "base": old, "target": new, "delta": new - old})
    stats.append(
        {
            "key": "tech_count",
            "label": "技术项",
            "base": len(base.get("techs") or []),
            "target": len(target.get("techs") or []),
            "delta": len(target.get("techs") or []) - len(base.get("techs") or []),
        }
    )

    text_sections = [
        _text_list_diff(base.get("risks"), target.get("risks"), "风险"),
        _text_list_diff(base.get("architecture"), target.get("architecture"), "架构"),
        _text_list_diff(base.get("highlights"), target.get("highlights"), "亮点"),
        _text_list_diff(base.get("learning_path"), target.get("learning_path"), "学习路径"),
    ]
    warning_diff = _text_list_diff(base.get("warnings"), target.get("warnings"), "警告")

    summary = {
        "tech_added": techs["added_count"],
        "tech_removed": techs["removed_count"],
        "tech_changed": techs["changed_count"],
        "module_nodes_added": modules["nodes_added_count"],
        "module_nodes_removed": modules["nodes_removed_count"],
        "module_edges_added": modules["edges_added_count"],
        "module_edges_removed": modules["edges_removed_count"],
        "risk_added": text_sections[0]["added_count"],
        "risk_removed": text_sections[0]["removed_count"],
        "warning_added": warning_diff["added_count"],
        "warning_removed": warning_diff["removed_count"],
        "loc_delta": int(new_stats.get("total_loc") or 0) - int(old_stats.get("total_loc") or 0),
        "file_delta": int(new_stats.get("file_count") or 0) - int(old_stats.get("file_count") or 0),
    }
    has_changes = any(
        summary[key]
        for key in (
            "tech_added",
            "tech_removed",
            "tech_changed",
            "module_nodes_added",
            "module_nodes_removed",
            "module_edges_added",
            "module_edges_removed",
            "risk_added",
            "risk_removed",
            "warning_added",
            "warning_removed",
            "loc_delta",
            "file_delta",
        )
    ) or any(
        section["added_count"] or section["removed_count"]
        for section in (*text_sections, warning_diff)
    )

    return {
        "base": {
            "run_id": _text(base.get("run_id")),
            "repo_name": _text(base.get("repo_name")),
            "source": _text(base.get("source")),
            "generated_at": _text(base.get("generated_at")),
            "schema_version": base.get("schema_version", 1),
        },
        "target": {
            "run_id": _text(target.get("run_id")),
            "repo_name": _text(target.get("repo_name")),
            "source": _text(target.get("source")),
            "generated_at": _text(target.get("generated_at")),
            "schema_version": target.get("schema_version", 1),
        },
        "same_repo": _text(base.get("source")) == _text(target.get("source")),
        "has_changes": has_changes,
        "summary": summary,
        "stats": stats,
        "techs": techs,
        "modules": modules,
        "text": {
            "risks": text_sections[0],
            "architecture": text_sections[1],
            "highlights": text_sections[2],
            "learning_path": text_sections[3],
            "warnings": warning_diff,
        },
    }
