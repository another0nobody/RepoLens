"""结构化输出（Structured Output）的数据模型。

【给初学者：什么是"结构化输出"？】
大模型默认返回一段自由文本，人类读起来舒服，但程序很难处理：
    "这个项目用了 FastAPI，大概还有 SQLAlchemy……"
如果网页想把它画成一张张卡片，就需要稳定的字段（name/category/role/...）。

LangChain 的做法是：给模型一份"表格模板"，让它按模板填写。
本文件里的 Pydantic 类就是那份模板：
    - Field(description=...) 是写给模型看的"填写说明"；
    - Literal[...] 限定只能填固定的几个值；
    - 模型填错时，框架会把错误信息返回给它，让它重填（详见 agent.py 的 handle_errors）。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# 这里的分类必须和 catalog.CATEGORIES 完全一致。
# 之所以手写一遍，是因为 Literal 需要"字面量"，不能直接引用运行时才得到的元组。
CategoryName = Literal[
    "编程语言",
    "前端框架",
    "后端框架",
    "AI & Agent",
    "数据库",
    "缓存与消息",
    "基础设施与运维",
    "测试与质量",
    "构建与工具链",
    "数据科学",
    "监控与观测",
    "其他依赖",
]
Confidence = Literal["高", "中", "低"]


class TechFinding(BaseModel):
    """某一项技术的"使用情况说明"。"""

    name: str = Field(
        description=(
            "技术名称。必须原样使用扫描结果里给出的名字，"
            "例如 FastAPI、React、PostgreSQL；不要自己编造或改写大小写。"
        )
    )
    category: CategoryName = Field(description="技术分类，只能从给定的分类中选择")
    role: str = Field(
        description=(
            "这项技术在这个仓库里具体承担什么职责，用 1~2 句中文说清楚，"
            "例如：'用 FastAPI 提供 /api 下的 REST 接口，并负责请求参数校验'。"
            "要结合模块路径说明，不要泛泛而谈。"
        )
    )
    key_modules: list[str] = Field(
        default_factory=list,
        description=(
            "最能体现这项技术的模块/文件相对路径，必须来自扫描结果，"
            "最多 6 个；找不到就留空数组。"
        ),
    )
    confidence: Confidence = Field(
        default="中",
        description="你对'这个项目确实使用了它'的判断把握：高/中/低",
    )


class RepoInsight(BaseModel):
    """Agent 最终交付给网页的"分析结论"。"""

    summary: str = Field(
        description=(
            "用 3~5 句中文概括：这是一个什么项目、主要用什么技术、"
            "代码大致怎么分层。必须基于扫描事实，不要写空话。"
        )
    )
    highlights: list[str] = Field(
        default_factory=list,
        description="2~5 条项目亮点或特点（例如：前后端分离、有 Docker 编排、测试齐全）",
    )
    architecture: list[str] = Field(
        default_factory=list,
        description=(
            "3~6 条架构说明，按'入口 -> 分层 -> 数据/外部依赖'的顺序描述，"
            "每条都要提到具体目录或文件。"
        ),
    )
    techs: list[TechFinding] = Field(
        description=(
            "技术栈清单。优先覆盖扫描结果里出现的技术，按重要程度排序；"
            "每项都要给出它在项目中的职责。"
        )
    )
    risks: list[str] = Field(
        default_factory=list,
        description=(
            "1~5 条值得注意的风险或改进建议，例如缺少依赖锁文件、"
            "敏感配置写在代码里、核心模块缺少测试。没有就留空数组。"
        ),
    )
    learning_path: list[str] = Field(
        default_factory=list,
        description=(
            "面向初学者的 3~6 步学习路线：先读哪个文件、再理解哪一层、"
            "最后可以动手改什么。要结合本仓库的真实路径。"
        ),
    )


def structured_output_error_handler(error: Exception) -> str:
    """结构化输出失败时，把错误翻译成"人话"再交还给模型。

    【为什么要自定义？】
    ToolStrategy 默认会把原始报错直接塞回给模型。报错里常常是一大段
    pydantic 的英文堆栈，模型容易懵。这里改成明确的中文提示，重试成功率更高。

    参数 error：LangChain 抛出的异常（例如 StructuredOutputValidationError）。
    返回：一段给模型看的纠错说明。
    """
    from langchain.agents.structured_output import (
        MultipleStructuredOutputsError,
        StructuredOutputValidationError,
    )

    if isinstance(error, MultipleStructuredOutputsError):
        return (
            "你一次给出了多个结构化结果。请只提交一个 RepoInsight，"
            "把其余内容合并进去，然后重新调用提交工具。"
        )
    if isinstance(error, StructuredOutputValidationError):
        return (
            "结构化结果没有通过校验：请检查 techs 里每项的 name/category/role 是否存在、"
            "category 是否使用了允许的中文分类、数组字段是否为数组。"
            f"原始错误摘要：{str(error)[:600]}"
        )
    return f"提交结构化结果时出错，请修正后重试。错误摘要：{str(error)[:600]}"
