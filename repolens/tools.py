"""暴露给 Agent 的工具（Tools）。

【给初学者：什么是 Agent 的 Tool？】
大模型本身只能"输出文字"，不能读文件、不能上网、不能执行 git。
Tool 就是"你允许 Agent 调用的一段 Python 函数"。

Agent 的工作循环大致是：
    模型思考 -> 决定调用某个工具（给出参数）-> 程序真正执行工具 -> 把结果还给模型 -> 再思考……
所以工具的"名字 + 参数说明 + docstring"写得越清楚，模型越不容易用错。

本项目一共有 6 个工具：
    1. clone_github_repository  克隆 GitHub 仓库（会触发人工审批）
    2. inspect_local_repository 检查并扫描本地目录
    3. list_technologies        列出扫描到的技术候选
    4. inspect_technology       查看某项技术的证据和模块（核心工具）
    5. read_project_file        读取仓库内某个文件的一小段（只读 + 脱敏）
    6. remember_analysis        把分析摘要写入长期记忆（跨会话保存）

注意：所有工具都是"只读"的，不会修改你的仓库。
"""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime

from . import sources
from .context import AnalysisContext
from .scanner import SnapshotError, get_tech_by_name, scan_repository
from .security import is_sensitive_path, mask_secrets
from .sources import SourceError, check_repo_size, clone_github, validate_local_path


def repo_overview(snapshot, note: str) -> dict:
    """扫描完成后，给模型一份"目录级别"的概览（不含每个技术的细节）。"""
    data = snapshot.to_dict()
    return {
        "repo_name": snapshot.repo_name,
        "root": str(snapshot.root),
        "note": note,
        "stats": data["stats"],
        "languages": [
            {"name": item["name"], "percent": item["percent"], "loc": item["loc"]}
            for item in snapshot.languages
            if item["is_code"]
        ][:8],
        "manifests": [item["path"] for item in data["manifests"][:10]],
        "entry_points": snapshot.entry_points[:8],
        "top_dirs": snapshot.top_dirs[:8],
        "tech_count": len(snapshot.techs),
        "tech_preview": [
            {
                "name": tech.name,
                "category": tech.category,
                "module_count": len(tech.modules),
            }
            for tech in snapshot.techs[:16]
        ],
        "instructions": (
            "仓库已准备好。接下来请调用 list_technologies 了解候选技术，"
            "再用 inspect_technology 核实重点技术的模块和证据，最后提交结构化报告。"
        ),
    }


def _prepare_repository(ctx: AnalysisContext, path: Path, source_type: str, note: str) -> str:
    """扫描仓库并把概览返回给模型。"""
    if ctx.snapshot is not None:
        return json.dumps(repo_overview(ctx.snapshot, ctx.source_note), ensure_ascii=False)

    ctx.progress(f"开始扫描：{path.name}")
    size_mb, too_big = check_repo_size(path)
    if too_big:
        ctx.progress(f"仓库约 {size_mb:.1f} MB，超过建议上限，将只扫描前面的文件")
        ctx.log(f"仓库体积约 {size_mb:.1f} MB，较大，扫描可能不完整", "warning")

    snapshot = scan_repository(
        root=path,
        source=ctx.source,
        source_type=source_type,
        progress=lambda message: ctx.progress(message),
    )
    ctx.repo_root = path
    ctx.snapshot = snapshot
    ctx.source_note = note

    overview = repo_overview(snapshot, note)
    ctx.emit("meta", overview)
    return json.dumps(overview, ensure_ascii=False)


def build_tools(ctx: AnalysisContext) -> list:
    """创建这一轮分析专用的工具列表。

    为什么要用函数包一层？因为工具需要访问 ctx（本次分析的上下文）。
    这里用了 Python 的"闭包"：里面的函数记住了外面的 ctx。
    """

    @tool(parse_docstring=True)
    def clone_github_repository(url: str) -> str:
        """从 GitHub 克隆一个公开仓库到本地缓存目录，然后扫描它。

        只有用户输入的是 GitHub 地址时才调用这个工具。
        这是唯一一个会访问网络的工具，执行前会要求用户在网页上批准。
        如果仓库之前已经克隆过，会直接复用本地缓存，不会重复下载。

        Args:
            url: GitHub 仓库地址，例如 https://github.com/psf/requests 或 psf/requests
        """
        if ctx.snapshot is not None:
            return json.dumps(repo_overview(ctx.snapshot, ctx.source_note), ensure_ascii=False)
        try:
            path, note = clone_github(url, progress=lambda message: ctx.progress(message))
            return _prepare_repository(ctx, path, "github", note)
        except SourceError as exc:
            ctx.error = str(exc)
            ctx.log(f"GitHub 仓库准备失败：{exc}", "error")
            return f"错误：{exc}"
        except Exception as exc:  # 兜底，避免整个 Agent 崩掉
            ctx.error = f"克隆或扫描仓库时出错：{exc}"
            ctx.log(ctx.error, "error")
            return f"错误：{ctx.error}"

    @tool(parse_docstring=True)
    def inspect_local_repository(path: str) -> str:
        """检查并扫描本机上的一个代码仓库目录。

        当用户给出的是本地路径（例如 C:\\code\\demo 或 ./examples/demo_shop）时调用。
        工具只读取文件，不会修改任何内容；会拒绝系统目录和磁盘根目录。

        Args:
            path: 本地仓库文件夹的绝对路径或相对路径
        """
        if ctx.snapshot is not None:
            return json.dumps(repo_overview(ctx.snapshot, ctx.source_note), ensure_ascii=False)
        try:
            repo_path = validate_local_path(path)
            return _prepare_repository(ctx, repo_path, "local", "本地目录")
        except SourceError as exc:
            ctx.error = str(exc)
            ctx.log(f"本地路径检查失败：{exc}", "error")
            return f"错误：{exc}"
        except SnapshotError as exc:
            ctx.error = str(exc)
            ctx.log(f"扫描失败：{exc}", "error")
            return f"错误：{exc}"
        except Exception as exc:
            ctx.error = f"扫描本地仓库时出错：{exc}"
            ctx.log(ctx.error, "error")
            return f"错误：{ctx.error}"

    @tool(parse_docstring=True)
    def list_technologies(category: str = "全部") -> str:
        """列出扫描器识别到的所有技术候选，按分类分组。

        在制定报告前先用它了解全貌。返回内容里包含：技术名、分类、版本、
        代码中使用它的模块数量。注意：模块数为 0 表示只在依赖清单/配置里出现。

        Args:
            category: 可选，只看某个分类，例如 "后端框架"、"数据库"；默认 "全部"
        """
        snapshot = ctx.snapshot
        if snapshot is None:
            return "错误：还没有扫描仓库。请先调用 inspect_local_repository 或 clone_github_repository。"
        techs = snapshot.techs
        if category and category not in {"全部", "all", "All"}:
            techs = [tech for tech in techs if tech.category == category]
        if not techs:
            return f"没有找到分类为 {category} 的技术。"

        lines = [f"共 {len(techs)} 项技术："]
        current_category = ""
        for tech in techs:
            if tech.category != current_category:
                current_category = tech.category
                lines.append(f"\n【{current_category}】")
            version = f" v{tech.version}" if tech.version else ""
            lines.append(
                f"- {tech.name}{version}（模块 {len(tech.modules)} 个，证据 {len(tech.evidence)} 条）"
            )
        return "\n".join(lines)[:6000]

    @tool(parse_docstring=True)
    def inspect_technology(names: list[str]) -> str:
        """查看一项或多项技术的详细证据：依赖声明位置、import 语句、使用它的模块路径。

        这是写报告前最重要的核实工具。建议一次传入 3~6 个技术名，分 2~3 批调用，
        不要对几十个技术逐个调用（会浪费时间和 token）。

        Args:
            names: 技术名称列表，例如 ["FastAPI", "SQLAlchemy", "PostgreSQL"]
        """
        snapshot = ctx.snapshot
        if snapshot is None:
            return "错误：还没有扫描仓库。请先调用 inspect_local_repository 或 clone_github_repository。"
        if isinstance(names, str):
            names = [names]
        if not isinstance(names, list):
            names = [str(names)]

        chunks: list[str] = []
        for raw_name in names[:8]:
            tech = get_tech_by_name(snapshot, str(raw_name))
            if tech is None:
                chunks.append(f"## {raw_name}\n未在扫描结果中找到这项技术。")
                continue
            lines = [
                f"## {tech.name}",
                f"分类：{tech.category}｜版本：{tech.version or '未知'}｜置信度：{tech.confidence}",
                f"说明：{tech.hint or '无'}",
            ]
            if tech.evidence:
                lines.append("证据：")
                for item in tech.evidence[:5]:
                    location = item["path"] if not item["line"] else f"{item['path']}:{item['line']}"
                    lines.append(f"- {location}｜{item['kind']}｜{item['text']}")
            if tech.modules:
                lines.append(f"使用它的模块（{len(tech.modules)} 个，展示前 10 个）：")
                for module in list(tech.modules.values())[:10]:
                    summary = f"｜{module['summary']}" if module.get("summary") else ""
                    lines.append(
                        f"- {module['path']}:{module['line']}｜{module['role']}{summary}｜{module['snippet']}"
                    )
                if tech.usage_tags:
                    lines.append(f"- 用途：{'、'.join(sorted(tech.usage_tags))}")
            else:
                lines.append("使用它的模块：没有找到直接 import（可能仅由配置/框架间接使用）。")
            chunks.append("\n".join(lines))
        return "\n\n".join(chunks)[:7000]

    @tool(parse_docstring=True)
    def read_project_file(relative_path: str, max_chars: int = 1800) -> str:
        """读取仓库内一个文本文件的一小段内容（只读，自动隐藏密钥）。

        适合读取 README、入口文件、配置文件，帮助理解项目用途。
        不要用它读二进制文件；也不要试图读取 .env、私钥等敏感文件（会被拒绝）。

        Args:
            relative_path: 相对于仓库根目录的文件路径，例如 "README.md" 或 "src/main.py"
            max_chars: 最多返回多少个字符，默认 1800
        """
        snapshot = ctx.snapshot
        if snapshot is None:
            return "错误：还没有扫描仓库。"
        if is_sensitive_path(relative_path):
            return "错误：出于安全考虑，不能读取 .env、私钥等敏感文件。"
        try:
            target = (snapshot.root / relative_path).resolve()
            target.relative_to(snapshot.root.resolve())
        except (OSError, ValueError):
            return "错误：只允许读取仓库内的文件。"
        if not target.is_file():
            return f"错误：文件不存在：{relative_path}"
        try:
            if target.stat().st_size > 400_000:
                return "错误：文件太大，请换一个更小的文件。"
            content = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return f"错误：读取失败（{exc}）"
        content, hits = mask_secrets(content)
        limit = max(200, min(int(max_chars or 1800), 4000))
        excerpt = content[:limit]
        suffix = "\n…（已截断）" if len(content) > limit else ""
        note = f"\n（已自动隐藏 {hits} 处疑似敏感信息）" if hits else ""
        return f"文件：{relative_path}{note}\n```\n{excerpt}{suffix}\n```"

    @tool(parse_docstring=True)
    def remember_analysis(summary: str, runtime: ToolRuntime) -> str:
        """把本次分析的结论写入长期记忆，方便以后在别的会话里回忆。

        长期记忆（Store）和短期记忆（Checkpointer）不同：
            - 短期记忆：同一个 thread_id 内的对话历史，进程重启就没了；
            - 长期记忆：按 namespace + key 保存，可跨会话、跨线程读取。

        Args:
            summary: 用 2~3 句话总结这个仓库的技术栈，便于以后检索
        """
        if ctx.snapshot is None:
            return "错误：还没有扫描仓库，暂不保存。"
        store = getattr(runtime, "store", None) or ctx.store
        if store is None:
            return "长期记忆未启用，已跳过保存。"
        run_id = (getattr(runtime, "state", None) or {}).get("run_id") or ctx.run_id
        namespace = ("repolens", "analyses")
        value = {
            "run_id": run_id,
            "repo_name": ctx.snapshot.repo_name,
            "source": ctx.source,
            "summary": summary[:800],
            "techs": [tech.name for tech in ctx.snapshot.techs[:10]],
        }
        try:
            store.put(namespace, str(run_id), value)
        except Exception as exc:
            return f"保存长期记忆失败：{exc}"
        return f"已写入长期记忆（namespace={namespace}，key={run_id}）。"

    return [
        clone_github_repository,
        inspect_local_repository,
        list_technologies,
        inspect_technology,
        read_project_file,
        remember_analysis,
    ]
