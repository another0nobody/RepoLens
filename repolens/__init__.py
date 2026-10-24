"""RepoLens：用 LangChain Agent 分析代码仓技术栈。

这个包里每个文件的分工（按阅读顺序）：

    config.py     读取 .env，决定用哪个大模型
    events.py     进程内的"事件总线"，把 Agent 的进度实时推给网页
    catalog.py    技术名词典：认识 100+ 常见框架/库/工具，并给它们分类
    scanner.py    纯 Python 的仓库扫描器（不调用大模型，保证结果可复现）
    schemas.py    结构化输出用的 Pydantic 模型
    tools.py      暴露给 Agent 的工具（Tool）
    middleware.py 自定义中间件（把 Agent 的每一步变成网页上的进度）
    agent.py      组装 Agent：模型 + 工具 + 中间件 + 结构化输出 + 记忆
    report.py     把"扫描结果"和"AI 解读"合并成最终报告
    server.py     零第三方依赖的 Web 服务器 + SSE 实时推送
"""

__version__ = "1.0.0"
__app_name__ = "RepoLens"
