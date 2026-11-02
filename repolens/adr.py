"""技术选型 ADR：把报告事实整理成可导出的中文 Markdown。"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from . import catalog


class AdrError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def _text(value: Any) -> str:
    return str(value or "").strip()


def _safe_filename(repo: str, tech: str) -> str:
    raw = f"adr-{repo or 'repo'}-{tech}".lower()
    cleaned = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", raw).strip("-")
    return f"{cleaned or 'adr'}.md"


def _find_tech(report: dict, name: str) -> dict:
    wanted = name.strip().lower()
    if not wanted:
        raise AdrError("请提供技术名称", 400)
    for tech in report.get("techs") or []:
        if not isinstance(tech, dict):
            continue
        if wanted == _text(tech.get("name")).lower() or wanted == _text(tech.get("key")).lower():
            return tech
    raise AdrError(f"报告中没有「{name}」", 404)


def _alternatives(tech: dict, report: dict) -> list[dict]:
    spec = catalog.lookup(_text(tech.get("name")))
    category = spec.category if spec else _text(tech.get("category"))
    project_names = {_text(item.get("name")).lower() for item in report.get("techs") or [] if isinstance(item, dict)}
    candidates = [
        item
        for item in catalog.CATALOG
        if item.category == category and item.name.lower() != _text(tech.get("name")).lower()
    ]
    # 优先给“项目里还没用”的候选；不足时再补项目内同类技术。
    candidates.sort(key=lambda item: (item.name.lower() in project_names, item.name))
    result = [{"name": item.name, "hint": item.hint, "in_project": item.name.lower() in project_names} for item in candidates[:5]]
    if len(result) < 2:
        seen = {item["name"] for item in result}
        for item in report.get("techs") or []:
            if not isinstance(item, dict):
                continue
            if _text(item.get("category")) != category or _text(item.get("name")) in seen:
                continue
            if _text(item.get("name")).lower() == _text(tech.get("name")).lower():
                continue
            result.append({"name": _text(item.get("name")), "hint": _text(item.get("hint")), "in_project": True})
            if len(result) >= 2:
                break
    return result[:5]


def _impact_lines(tech: dict) -> tuple[list[str], list[str]]:
    tags = set(tech.get("usage_tags") or [])
    modules = tech.get("modules") or []
    confidence = _text(tech.get("confidence")) or "未知"
    positives = [
        f"项目已有 {len(modules)} 个模块直接使用 {tech.get('name')}，说明它已进入实际代码路径。"
        if modules
        else f"{tech.get('name')} 已在依赖/配置中出现，但尚未找到直接 import。",
        "本次报告保留了依赖、import、代码使用和模块位置，替换或升级时可以按证据逐项核对。",
    ]
    if "缓存" in tags:
        positives.append("缓存用途通常用于降低重复查询的延迟；实际收益仍需结合命中率和数据一致性验证。")
    if "消息" in tags:
        positives.append("消息用途通常用于解耦异步任务；需要额外关注重试、幂等和积压。")
    costs = [
        f"当前置信度为「{confidence}」；置信度不等于生产稳定性，仍需人工确认版本与使用方式。",
        "报告没有记录性能基准、成本、团队熟悉度或合规要求，不能据此断言这是最优选型。",
    ]
    if modules:
        costs.append("替换这项技术时，至少需要同步检查上述直接使用它的模块。")
    if not modules:
        costs.append("如果它只出现在依赖清单，先确认是否仍在运行路径中，避免为未使用依赖写 ADR。")
    return positives, costs


def build_adr(report: dict, tech_name: str) -> dict:
    tech = _find_tech(report, tech_name)
    spec = catalog.lookup(_text(tech.get("name")))
    alternatives = _alternatives(tech, report)
    positives, costs = _impact_lines(tech)
    repo_name = _text(report.get("repo_name")) or "未命名仓库"
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    modules = tech.get("modules") or []
    evidence = tech.get("evidence") or []
    tags = "、".join(tech.get("usage_tags") or []) or "未细分"

    lines = [
        f"# ADR：采用 {tech.get('name')} 作为「{tech.get('function') or tech.get('category') or '项目能力'}」",
        "",
        f"- 状态：提议（待团队确认）",
        f"- 项目：{repo_name}",
        f"- 报告：{_text(report.get('run_id'))}",
        f"- 生成时间：{generated_at}",
        f"- 技术：{tech.get('name')}",
        f"- 层级：{tech.get('layer') or tech.get('category') or '未分类'}",
        f"- 功能：{tech.get('function') or tech.get('category') or '未分类'}",
        f"- 置信度：{tech.get('confidence') or '未知'}",
        f"- 用途：{tags}",
        "",
        "## 背景",
        "",
        f"RepoLens 在 `{repo_name}` 中识别到 **{tech.get('name')}**，归类为「{tech.get('category') or '未分类'}」。",
        f"扫描事实显示：{len(modules)} 个模块直接使用它，记录到 {len(evidence)} 条证据；用途标签为「{tags}」。",
        "",
        "> 说明：本 ADR 由报告事实生成。仓库没有明确记录选型动机，因此下文不会编造“团队为什么选它”。",
        "",
        "## 决策",
        "",
        f"将 **{tech.get('name')}** 视为本项目「{tech.get('function') or tech.get('category') or '相关能力'}」的实现技术，"
        f"并在后续维护中按模块证据核对它的实际使用范围。",
        "",
        f"技术说明：{_text(tech.get('hint')) or (spec.hint if spec else '词典未收录这项技术的说明。')}",
        "",
        "## 备选方案",
        "",
        "| 方案 | 定位 | 项目状态 |",
        "| --- | --- | --- |",
    ]
    if alternatives:
        for item in alternatives:
            state = "项目内已有" if item["in_project"] else "项目内未识别"
            lines.append(f"| {item['name']} | {item['hint'] or '词典暂无说明'} | {state} |")
    else:
        lines.append("| 暂无 | 词典中没有找到同类候选 | — |")
    lines.extend(
        [
            "",
            "> 备选方案来自技术词典的同类分类，不代表团队真实比较过这些方案。",
            "",
            "## 后果",
            "",
            "### 正面",
            "",
            *[f"- {item}" for item in positives],
            "",
            "### 代价与风险",
            "",
            *[f"- {item}" for item in costs],
            "",
            "## 证据",
            "",
        ]
    )
    if evidence:
        for item in evidence[:8]:
            lines.append(
                f"- `{item.get('path')}:{item.get('line')}`（{item.get('kind') or '证据'}）：{_text(item.get('text'))[:160]}"
            )
    else:
        lines.append("- 暂无代码证据。")
    if modules:
        lines.extend(["", "## 使用模块", ""])
        for module in modules[:10]:
            lines.append(
                f"- `{module.get('path')}:{module.get('line')}`（{module.get('role') or '源码'}）"
                + (f"：{module.get('summary')}" if module.get("summary") else "")
            )
    lines.extend(
        [
            "",
            "## 待确认",
            "",
            f"- 为什么选择 {tech.get('name')}，而不是上面列出的同类方案？仓库中没有记录。",
            "- 当前版本是否仍受维护？是否有升级或迁移计划？",
            "- 是否有性能、成本、合规或团队熟悉度方面的约束？",
            "",
            "---",
            "由 RepoLens 基于扫描事实生成；请把推断内容替换为团队确认后的决策记录。",
            "",
        ]
    )
    markdown = "\n".join(lines)
    return {
        "tech": tech.get("name"),
        "filename": _safe_filename(repo_name, _text(tech.get("name"))),
        "markdown": markdown,
        "alternatives": alternatives,
        "generated_at": generated_at,
    }
