"""把"扫描事实"和"AI 解读"合并成网页要展示的最终报告。

【给初学者：为什么要合并？】
Agent 负责理解和表达，但它有可能漏掉某项技术、写错模块路径，甚至多写一个不存在的技术。
扫描器负责精确，但它不会写"这项技术在项目里起什么作用"。

所以最终报告 = 扫描器的事实（技术、版本、证据、模块） + Agent 的解释（职责、摘要、架构、风险）。
合并时我们做三件事：
    1. 以扫描结果为准，保证不漏、不假；
    2. 把 AI 写的职责/模块贴到对应技术上；
    3. AI 多写的技术标记为"AI 推断"，让用户知道它没有代码证据。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from . import catalog, config
from .context import AnalysisContext
from .scanner import Snapshot, TechHit, guess_module_role

MAX_FACTS_CHARS = 7000

# 报告结构版本：
#   1：早期没有版本号的报告；
#   2：增加 function/function_order、layer/layer_order 等展示字段；
#   3：增加 module_graph（文件级依赖图）。
REPORT_SCHEMA_VERSION = 3


# ============================================================================
# 给 Agent 看的"事实摘要"
# ============================================================================
def build_facts_text(snapshot: Snapshot) -> str:
    """把扫描结果压缩成一段给模型看的文本（控制在 7000 字以内）。"""
    lines: list[str] = []
    languages = [item for item in snapshot.languages if item["is_code"]]
    language_text = "、".join(
        f"{item['name']} {item['loc']} 行（{item['percent']}%）" for item in languages[:6]
    ) or "未识别到代码语言"
    stats = snapshot.to_dict()["stats"]

    lines.append(f"仓库名称：{snapshot.repo_name}")
    lines.append(f"来源：{snapshot.source}（{snapshot.source_type}）")
    lines.append(
        f"规模：{stats['file_count']} 个文件，其中 {stats['code_file_count']} 个代码文件，"
        f"约 {stats['total_loc']} 行代码，{stats['size_mb']} MB"
    )
    lines.append(f"主要语言：{language_text}")

    manifests = snapshot.manifests[:8]
    if manifests:
        manifest_text = "、".join(f"{item.path}（{len(item.deps)} 条依赖）" for item in manifests)
        lines.append(f"依赖清单：{manifest_text}")
    else:
        lines.append("依赖清单：未找到常见依赖清单文件，技术识别主要依赖 import 扫描")

    if snapshot.top_dirs:
        dir_text = "、".join(f"{item['name']}/（{item['files']} 个文件）" for item in snapshot.top_dirs[:8])
        lines.append(f"主要目录：{dir_text}")
    if snapshot.entry_points:
        lines.append("可能的入口/关键文件：" + "、".join(snapshot.entry_points[:8]))
    if snapshot.truncated:
        lines.append("注意：仓库文件过多，扫描已被截断，报告只覆盖已扫描部分。")
    if snapshot.omitted_dependencies:
        lines.append(f"注意：还有 {snapshot.omitted_dependencies} 个词典未收录的小众依赖没有列出。")

    core = sorted(
        [tech for tech in snapshot.techs if tech.modules and tech.category != "编程语言"],
        key=lambda tech: (len(tech.modules), tech.confidence == "高"),
        reverse=True,
    )
    others = [
        tech
        for tech in snapshot.techs
        if tech not in core and tech.category not in {"编程语言", "其他依赖"}
    ]
    generic = [tech for tech in snapshot.techs if tech.category == "其他依赖"]

    lines.append("")
    lines.append("== 已扫描到的技术（name 必须原样使用；模块数=代码中直接 import 该技术的文件数）==")
    shown = 0
    for tech in core[:26]:
        lines.append(
            f"- {tech.name}｜{tech.category}｜版本 {tech.version or '未知'}｜"
            f"模块 {len(tech.modules)} 个｜证据 {len(tech.evidence)} 条"
        )
        shown += 1
    for tech in others[:14]:
        if tech in core:
            continue
        lines.append(
            f"- {tech.name}｜{tech.category}｜版本 {tech.version or '未知'}｜"
            f"模块 {len(tech.modules)} 个｜证据 {len(tech.evidence)} 条（仅依赖声明）"
        )
        shown += 1
    for tech in generic[:5]:
        lines.append(f"- {tech.name}｜其他依赖｜版本 {tech.version or '未知'}｜（词典未收录）")
        shown += 1
    if not shown:
        lines.append("- 暂无")
    lines.append(
        f"（共 {len(snapshot.techs)} 项；调用 inspect_technology 可以查看任意技术的证据与模块路径）"
    )

    if snapshot.readme.strip():
        readme = re.sub(r"\n{3,}", "\n\n", snapshot.readme.strip())[:900]
        lines.append("")
        lines.append("== README 片段 ==")
        lines.append(readme)

    text = "\n".join(lines)
    if len(text) > MAX_FACTS_CHARS:
        text = text[:MAX_FACTS_CHARS].rstrip() + "\n…（内容过长已截断）"
    return text


# ============================================================================
# 兜底文案（没有 AI 时也能出一份像样的报告）
# ============================================================================
_CATEGORY_ROLE = {
    "编程语言": "项目的主要开发语言之一。",
    "前端框架": "用于构建前端界面与交互。",
    "后端框架": "用于搭建后端服务、接口或数据校验。",
    "AI & Agent": "用于大模型、Agent 或向量检索相关能力。",
    "数据库": "用于业务数据的存储、建模或访问。",
    "缓存与消息": "用于缓存、会话或异步任务/消息处理。",
    "基础设施与运维": "用于构建、部署或运行环境的支撑。",
    "测试与质量": "用于自动化测试、代码检查或格式化。",
    "构建与工具链": "用于依赖管理与构建流程。",
    "数据科学": "用于数据处理、分析或可视化。",
    "监控与观测": "用于日志、指标、追踪或错误监控。",
    "其他依赖": "项目引入的第三方依赖。",
}


_FUNCTION_LAYER = {
    "构建前端界面": "前端",
    "调用后端接口": "前端",
    "提供后端接口": "后端",
    "持久化业务数据": "数据与存储",
    "提供数据缓存": "数据与存储",
    "提供会话存储": "数据与存储",
    "提供限流": "数据与存储",
    "提供向量检索": "数据与存储",
    "提供消息队列": "数据与存储",
    "编排 Agent": "Agent / AI",
    "调用大模型": "Agent / AI",
    "开发语言": "语言与运行时",
    "运行与部署": "基础设施",
    "监控与观测": "基础设施",
    "验证代码行为": "工程效率",
    "构建与工具链": "工程效率",
    "处理与分析数据": "数据与存储",
    "其他能力": "其他",
}

_LAYER_ORDER = {
    "前端": 10,
    "后端": 20,
    "数据与存储": 30,
    "Agent / AI": 40,
    "语言与运行时": 50,
    "基础设施": 60,
    "工程效率": 70,
    "其他": 999,
}

_FUNCTION_ORDER = {
    "开发语言": 10,
    "提供后端接口": 20,
    "持久化业务数据": 30,
    "提供数据缓存": 40,
    "提供会话存储": 41,
    "提供限流": 42,
    "提供向量检索": 43,
    "提供消息队列": 44,
    "构建前端界面": 50,
    "调用后端接口": 51,
    "编排 Agent": 60,
    "调用大模型": 61,
    "验证代码行为": 70,
    "监控与观测": 80,
    "运行与部署": 90,
    "构建与工具链": 100,
    "处理与分析数据": 110,
    "其他能力": 999,
}

_LLM_NAMES = {
    "OpenAI", "OpenAI SDK", "Azure OpenAI", "Anthropic", "Google Gemini",
    "DeepSeek", "Ollama", "Mistral AI", "Cohere",
}
_HTTP_CLIENT_NAMES = {"Axios", "fetch", "ky", "requests", "httpx", "HTTPX"}
_AGENT_NAMES = {"LangChain", "LangGraph", "LlamaIndex", "CrewAI", "AutoGen"}

_MESSAGE_NAMES = {
    "Kafka", "RabbitMQ", "NATS", "Apache Pulsar", "RocketMQ", "ZeroMQ",
}


def function_for(category: str, name: str, tags: list[str] | set[str] | None = None) -> str:
    """把“技术分类”翻译成用户先理解的项目功能。

    例如 Redis + 缓存标签 → “提供数据缓存”，FastAPI → “提供后端接口”。
    这是展示层的主分组键，不替代原始 category。
    """
    tags = set(tags or [])
    if name in _LLM_NAMES:
        return "调用大模型"
    if name in _AGENT_NAMES:
        return "编排 Agent"
    if name in _HTTP_CLIENT_NAMES:
        return "调用后端接口"
    if category == "缓存与消息":
        if "消息" in tags or name in _MESSAGE_NAMES:
            return "提供消息队列"
        if "会话" in tags:
            return "提供会话存储"
        if "限流" in tags:
            return "提供限流"
        if "向量" in tags:
            return "提供向量检索"
        return "提供数据缓存"
    return {
        "编程语言": "开发语言",
        "后端框架": "提供后端接口",
        "前端框架": "构建前端界面",
        "AI & Agent": "编排 Agent",
        "数据库": "持久化业务数据",
        "测试与质量": "验证代码行为",
        "基础设施与运维": "运行与部署",
        "构建与工具链": "构建与工具链",
        "监控与观测": "监控与观测",
        "数据科学": "处理与分析数据",
    }.get(category, "其他能力")


def layer_for(function: str) -> str:
    """把功能归到前/后/数据/AI/基础设施等层级。"""
    return _FUNCTION_LAYER.get(function, "其他")


def default_function(tech: TechHit) -> str:
    return function_for(tech.category, tech.name, tech.usage_tags)


def default_role(tech: TechHit) -> str:
    base = _CATEGORY_ROLE.get(tech.category, "项目使用的技术之一。")
    if tech.category == "编程语言":
        return f"{tech.name} 是本项目的主要开发语言之一。"
    hint = f"（{tech.hint}）" if tech.hint else ""
    tags = "、".join(sorted(tech.usage_tags))
    if tags and tech.modules:
        return f"在项目中作为{tags}使用{hint}，在 {len(tech.modules)} 个模块中被直接使用。"
    if tags:
        return f"在项目中作为{tags}使用{hint}。"
    if tech.modules:
        return f"{base.rstrip('。')}{hint}，在 {len(tech.modules)} 个模块中被直接使用。"
    return f"{base.rstrip('。')}{hint}，主要在依赖清单或配置中出现。"


def _top_techs(snapshot: Snapshot, limit: int = 5) -> list[TechHit]:
    candidates = [
        tech
        for tech in snapshot.techs
        if tech.category not in {"编程语言", "其他依赖"}
    ]
    candidates.sort(
        key=lambda tech: (
            tech.category not in {"后端框架", "前端框架", "AI & Agent", "数据库"},
            -len(tech.modules),
            tech.confidence != "高",
        )
    )
    return candidates[:limit]


def deterministic_summary(snapshot: Snapshot) -> str:
    languages = [item for item in snapshot.languages if item["is_code"]][:3]
    language_text = "、".join(f"{item['name']}（{item['percent']}%）" for item in languages) or "暂未识别的语言"
    top = _top_techs(snapshot, 5)
    top_text = "、".join(tech.name for tech in top) or "暂无明确的核心框架"
    stats = snapshot.to_dict()["stats"]

    first_line = ""
    for line in snapshot.readme.splitlines():
        cleaned = line.strip().lstrip("#").strip()
        if cleaned and not cleaned.startswith(("![", "[!", "<")):
            first_line = cleaned[:80]
            break

    summary = (
        f"{snapshot.repo_name} 是一个以 {language_text} 为主的项目，"
        f"共扫描 {stats['code_file_count']} 个代码文件、约 {stats['total_loc']} 行代码。"
        f"检测到 {len(snapshot.techs)} 项技术，核心包括 {top_text}。"
    )
    if first_line:
        summary += f" 项目自述：{first_line}。"
    return summary


def deterministic_highlights(snapshot: Snapshot) -> list[str]:
    names = {tech.name for tech in snapshot.techs}
    highlights: list[str] = []
    if {"FastAPI", "React", "Vue.js", "Next.js", "Express", "Django", "Flask"} & names:
        if any(name in names for name in ("React", "Vue.js", "Next.js")):
            highlights.append("包含独立的前端工程，前后端通过 HTTP 接口协作。")
    if {"Docker", "Docker Compose"} & names:
        highlights.append("提供了容器化配置，可以用 Docker 一键拉起运行环境。")
    if any(tech.category == "AI & Agent" for tech in snapshot.techs):
        highlights.append("包含 AI / Agent 相关技术，可能涉及大模型调用或 RAG。")
    if any(tech.name == "pytest" for tech in snapshot.techs):
        highlights.append("包含 pytest 测试，便于验证核心逻辑。")
    if len(snapshot.languages) >= 3:
        highlights.append(f"仓库涉及 {len(snapshot.languages)} 种语言/文件类型，工程结构较丰富。")
    if not highlights:
        highlights.append("项目结构相对简单，适合作为阅读源码的起点。")
    return highlights[:5]


def deterministic_architecture(snapshot: Snapshot) -> list[str]:
    notes: list[str] = []
    if snapshot.entry_points:
        notes.append("入口/关键文件：" + "、".join(snapshot.entry_points[:5]) + "。")
    if snapshot.top_dirs:
        parts = [f"{item['name']}/（{item['files']} 个文件）" for item in snapshot.top_dirs[:4]]
        notes.append("主要目录：" + "、".join(parts) + "。")
    backend = [tech.name for tech in snapshot.techs if tech.category == "后端框架"][:3]
    frontend = [tech.name for tech in snapshot.techs if tech.category == "前端框架"][:3]
    if backend:
        notes.append("后端技术：" + "、".join(backend) + "。")
    if frontend:
        notes.append("前端技术：" + "、".join(frontend) + "。")
    if snapshot.manifests:
        notes.append("依赖与运行配置：" + "、".join(item.path for item in snapshot.manifests[:4]) + "。")
    if not notes:
        notes.append("未发现明显的分层目录，代码可能集中在少数文件中。")
    return notes[:6]


def deterministic_risks(snapshot: Snapshot) -> list[str]:
    risks: list[str] = []
    lock_files = {
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "poetry.lock",
        "uv.lock",
        "cargo.lock",
        "pipfile.lock",
        "go.sum",
    }
    if snapshot.manifests and not any(path.lower().rsplit("/", 1)[-1] in lock_files for path in snapshot.files):
        risks.append("没有发现依赖锁文件，不同机器安装到的版本可能不一致，建议提交 lock 文件。")
    if snapshot.truncated:
        risks.append("仓库文件数量超过扫描上限，本报告只覆盖部分文件，可能漏掉少数技术。")
    declared_only = [
        tech
        for tech in snapshot.techs
        if tech.category not in {"编程语言", "其他依赖"} and not tech.modules
    ]
    if len(declared_only) >= 4:
        risks.append(
            f"有 {len(declared_only)} 项技术只在依赖清单中出现、没有找到直接 import，"
            "它们可能由框架间接使用，也可能已经废弃。"
        )
    if snapshot.omitted_dependencies:
        risks.append(
            f"还有 {snapshot.omitted_dependencies} 个词典未收录的依赖没有展示，"
            "如果它们很重要，可以在源码里搜索确认。"
        )
    if not snapshot.manifests:
        risks.append("没有找到依赖清单文件，技术识别依赖 import 推断，可能不完整。")
    return risks[:5]


def deterministic_learning_path(snapshot: Snapshot) -> list[str]:
    path: list[str] = []
    entry_candidates = [item for item in snapshot.entry_points if item.lower().endswith((".py", ".js", ".ts", ".go", ".java", ".rs", ".tsx", ".vue"))]
    if entry_candidates:
        path.append(f"先打开入口文件 {entry_candidates[0]}，顺着 import 看请求是怎么进入业务的。")
    top_tech = _top_techs(snapshot, 3)
    for tech in top_tech:
        if tech.modules:
            first_module = sorted(tech.modules.values(), key=lambda item: item["path"])[0]
            path.append(f"找到 {first_module['path']}，观察 {tech.name} 在这里承担了什么职责。")
    if snapshot.entry_points:
        manifest = next((item for item in snapshot.entry_points if item.endswith((".txt", ".json", ".toml", ".mod"))), None)
        if manifest:
            path.append(f"阅读 {manifest}，理解项目依赖了哪些第三方能力。")
    path.append("尝试启动项目或运行测试，再用调试器跟一遍最核心的接口。")
    return path[:6]


# ============================================================================
# 合并
# ============================================================================
def _normalize(name: str) -> str:
    return catalog.normalize_name(name)


def _tech_aliases(tech: TechHit) -> set[str]:
    aliases = {_normalize(tech.name), tech.key}
    spec = catalog.lookup(tech.name)
    if spec is not None:
        aliases.add(_normalize(spec.name))
        aliases.update(_normalize(alias) for alias in spec.aliases)
    return {item for item in aliases if item}


def _find_snapshot_tech(snapshot: Snapshot, name: str) -> TechHit | None:
    wanted = _normalize(name)
    for tech in snapshot.techs:
        if wanted in _tech_aliases(tech):
            return tech
    # 再宽松一点：允许 "React.js" 之类
    if len(wanted) >= 4:
        for tech in snapshot.techs:
            for alias in _tech_aliases(tech):
                if len(alias) >= 4 and (wanted in alias or alias in wanted):
                    return tech
    return None


def _sorted_techs(techs: list[dict]) -> list[dict]:
    order = {name: index for index, name in enumerate(catalog.CATEGORIES)}
    return sorted(
        techs,
        key=lambda item: (
            order.get(item["category"], 99),
            item.get("ai_inferred", False),
            -item.get("module_count", 0),
            item["name"].lower(),
        ),
    )


def build_report(ctx: AnalysisContext, insight: Any = None, ai_error: str | None = None) -> dict:
    """合并扫描结果与 AI 结论，返回可 JSON 序列化的报告。"""
    snapshot = ctx.snapshot
    if snapshot is None:
        raise ValueError("没有扫描结果，无法生成报告")

    tech_dicts: list[dict] = []
    tech_by_key: dict[str, dict] = {}
    for tech in snapshot.techs:
        item = tech.to_dict()
        item["role"] = default_role(tech)
        item["key_modules"] = [module["path"] for module in item["modules"][:6]]
        item["ai_inferred"] = False
        tech_dicts.append(item)
        tech_by_key[tech.key] = item

    ai_added: list[str] = []
    ai_notes: list[dict] = []
    if insight is not None:
        raw_techs = getattr(insight, "techs", None) or []
        seen_ai: set[str] = set()
        for finding in raw_techs:
            name = getattr(finding, "name", "") or ""
            if not name:
                continue
            matched = _find_snapshot_tech(snapshot, name)
            if matched is not None:
                item = tech_by_key.get(matched.key)
                if item is None:
                    continue
                role = (getattr(finding, "role", "") or "").strip()
                if role:
                    item["role"] = role[:400]
                category = getattr(finding, "category", "")
                if category in catalog.CATEGORIES:
                    if item["category"] == "其他依赖" or item["category"] == category:
                        item["category"] = category
                key_modules = getattr(finding, "key_modules", None) or []
                valid = [path for path in key_modules if path in snapshot.files]
                if valid:
                    item["key_modules"] = valid[:6]
                    rank = {path: index for index, path in enumerate(valid)}
                    item["modules"].sort(key=lambda module: (module["path"] not in rank, rank.get(module["path"], 99)))
                item["ai_role"] = True
                item["ai_confidence"] = getattr(finding, "confidence", "中")
                seen_ai.add(matched.key)
            else:
                key = _normalize(name)
                if key in seen_ai:
                    continue
                seen_ai.add(key)
                category = getattr(finding, "category", "")
                if category not in catalog.CATEGORIES:
                    category = catalog.guess_generic_category(name)
                ai_added.append(name)
                tech_dicts.append(
                    {
                        "key": key,
                        "name": name,
                        "category": category,
                        "hint": "AI 根据上下文推断，代码中未找到直接证据",
                        "version": "",
                        "confidence": "低",
                        "sources": ["ai"],
                        "evidence": [],
                        "modules": [],
                        "module_count": 0,
                        "role": (getattr(finding, "role", "") or "由模型推断的技术，建议人工确认。")[:400],
                        "key_modules": [],
                        "ai_inferred": True,
                        "ai_role": True,
                        "ai_confidence": getattr(finding, "confidence", "低"),
                    }
                )
        ai_notes = [tech.model_dump() for tech in raw_techs if hasattr(tech, "model_dump")]

    # 功能 → 技术栈：在 AI 合并之后统一补上，保证 AI 改分类/AI 新增的技术也有主分组。
    for item in tech_dicts:
        function = function_for(item.get("category", ""), item.get("name", ""), item.get("usage_tags") or [])
        layer = layer_for(function)
        item["function"] = function
        item["function_order"] = _FUNCTION_ORDER.get(function, 999)
        item["layer"] = layer
        item["layer_order"] = _LAYER_ORDER.get(layer, 999)

    tech_dicts = _sorted_techs(tech_dicts)

    categories: list[dict] = []
    for category in catalog.CATEGORIES:
        items = [item for item in tech_dicts if item["category"] == category]
        if items:
            categories.append(
                {
                    "name": category,
                    "icon": catalog.CATEGORY_ICONS.get(category, "📦"),
                    "count": len(items),
                    "module_count": sum(item["module_count"] for item in items),
                }
            )

    stats = snapshot.to_dict()["stats"]
    warnings: list[str] = []
    if stats.get("truncated"):
        warnings.append("仓库文件过多，扫描已截断，报告只覆盖已扫描部分。")
    if ai_error:
        warnings.append(f"AI 解读失败，本报告由规则扫描兜底生成：{ai_error[:300]}")
    if insight is None and not ai_error:
        warnings.append("本次没有使用 AI 解读，报告仅基于静态扫描。")
    if ai_added:
        warnings.append(
            f"有 {len(ai_added)} 项技术是 AI 推断的，代码中没有找到直接证据："
            + "、".join(ai_added[:6])
        )

    summary = (getattr(insight, "summary", "") or "").strip() if insight is not None else ""
    architecture = list(getattr(insight, "architecture", None) or []) if insight is not None else []
    risks = list(getattr(insight, "risks", None) or []) if insight is not None else []
    learning_path = list(getattr(insight, "learning_path", None) or []) if insight is not None else []
    highlights = list(getattr(insight, "highlights", None) or []) if insight is not None else []

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": ctx.run_id,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "repo_name": snapshot.repo_name,
        "source": ctx.source,
        "source_type": ctx.source_type,
        "local_path": str(snapshot.root),
        "source_note": ctx.source_note,
        "summary": summary or deterministic_summary(snapshot),
        "highlights": highlights or deterministic_highlights(snapshot),
        "architecture": architecture or deterministic_architecture(snapshot),
        "risks": risks or deterministic_risks(snapshot),
        "learning_path": learning_path or deterministic_learning_path(snapshot),
        "stats": stats,
        "languages": snapshot.languages,
        "manifests": [
            {"path": item.path, "kind": item.kind, "dependency_count": len(item.deps), "note": item.note}
            for item in snapshot.manifests
        ],
        "top_dirs": snapshot.top_dirs,
        "entry_points": snapshot.entry_points,
        "techs": tech_dicts,
        "categories": categories,
        "module_graph": snapshot.module_graph,
        "warnings": warnings,
        "ai": {
            "used": insight is not None,
            "model": ctx.model_display,
            "error": ai_error,
            "inferred_techs": ai_added,
            "raw": ai_notes,
        },
    }
    return report


# ============================================================================
# 持久化
# ============================================================================
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def report_path(run_id: str) -> Path:
    if not _RUN_ID_RE.match(run_id):
        raise ValueError("非法的报告 ID")
    return config.REPORTS_DIR / f"{run_id}.json"


def normalize_report(report: dict) -> dict:
    """把旧报告补齐到当前 schema，保证前端字段稳定。

    旧版本没有 schema_version，也可能没有 function/layer。
    这里不删除任何旧字段，只补默认值和展示分组字段。
    """
    normalized = dict(report)
    normalized["schema_version"] = REPORT_SCHEMA_VERSION
    normalized.setdefault("warnings", [])
    normalized.setdefault("highlights", [])
    normalized.setdefault("risks", [])
    normalized.setdefault("learning_path", [])
    normalized.setdefault("architecture", [])
    normalized.setdefault("stats", {})
    normalized.setdefault("ai", {})
    normalized.setdefault("categories", [])
    normalized.setdefault("module_graph", {"nodes": [], "edges": [], "stats": {}})

    techs: list[dict] = []
    for raw in normalized.get("techs") or []:
        if not isinstance(raw, dict):
            continue
        tech = dict(raw)
        tags = tech.get("usage_tags") or []
        tech["usage_tags"] = sorted({str(tag) for tag in tags})
        function = str(tech.get("function") or "").strip()
        if not function:
            function = function_for(str(tech.get("category") or ""), str(tech.get("name") or ""), tags)
        layer = str(tech.get("layer") or "").strip() or layer_for(function)
        tech["function"] = function
        tech["function_order"] = int(tech.get("function_order") or _FUNCTION_ORDER.get(function, 999))
        tech["layer"] = layer
        tech["layer_order"] = int(tech.get("layer_order") or _LAYER_ORDER.get(layer, 999))
        tech["sources"] = tech.get("sources") or []
        tech["evidence"] = tech.get("evidence") or []
        tech["modules"] = tech.get("modules") or []
        tech["module_count"] = int(tech.get("module_count") or len(tech["modules"]))
        techs.append(tech)
    normalized["techs"] = techs
    return normalized


def save_report(report: dict, storage: Any = None) -> Path:
    normalized = normalize_report(report)
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = report_path(normalized["run_id"])
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    if storage is not None:
        try:
            storage.save_report(normalized)
        except Exception:
            # 文件报告已经保存；SQLite 失败不应让分析失败。
            pass
    return path


def load_report(run_id: str, storage: Any = None) -> dict | None:
    data: dict | None = None
    if storage is not None:
        try:
            data = storage.load_report(run_id)
        except Exception:
            data = None
    if data is None:
        try:
            path = report_path(run_id)
        except ValueError:
            return None
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return normalize_report(data) if isinstance(data, dict) else None


def list_reports(limit: int = 40) -> list[dict]:
    """列出历史报告（只读摘要，不返回完整内容）。"""
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    items: list[dict] = []
    for path in config.REPORTS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        items.append(
            {
                "run_id": data.get("run_id", path.stem),
                "schema_version": data.get("schema_version", 1),
                "repo_name": data.get("repo_name", path.stem),
                "source": data.get("source", ""),
                "source_type": data.get("source_type", ""),
                "generated_at": data.get("generated_at", ""),
                "tech_count": len(data.get("techs") or []),
                "code_files": (data.get("stats") or {}).get("code_file_count", 0),
                "total_loc": (data.get("stats") or {}).get("total_loc", 0),
                "ai_used": bool((data.get("ai") or {}).get("used")),
            }
        )
    items.sort(key=lambda item: item.get("generated_at", ""), reverse=True)
    return items[:limit]


def module_role(path: str) -> str:
    """给网页用的模块角色（复用了扫描器的启发式规则）。"""
    return guess_module_role(path)
