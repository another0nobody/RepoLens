# RepoLens 代码文档

> 面向维护者与 AI Agent 的「项目实现说明书」。
>
> 基线代码：`main` 分支（文档创建时的最新提交）。本文描述**已经实现的行为**，不是未来规划。
> 需求与验收标准见 [REQUIREMENTS.md](REQUIREMENTS.md)；Agent 的最短入口见根目录 [AGENTS.md](../AGENTS.md)。

---

## 0. 给 Agent 的阅读协议

在修改任何代码之前，请按这个顺序读：

1. [REQUIREMENTS.md](REQUIREMENTS.md)：知道哪些功能是 P0、不能删；
2. 本文：知道每个文件在哪、数据怎么流；
3. [README.md](../README.md)：知道面向用户的启动方式与教程映射；
4. 目标文件本身：不要只凭文档猜实现。

三条硬规则：

- **文档与代码冲突时，先记录冲突，再以代码现状为准**；不要为了让文档“看起来对”而删功能。
- 任何 API 字段、SSE 事件、报告 JSON 字段、前端状态字段的改动，必须同步修改本文和需求文档。
- 任何 P0 功能删除或降级，必须得到人类明确确认；否则视为回归。

---

## 1. 系统概览

RepoLens 是一个本地运行的「代码仓技术栈侦探」：

- 输入本地目录或 GitHub 仓库；
- 扫描依赖清单、源码 import、语言、目录结构；
- LangChain Agent 按工具流程核实技术；
- 输出可交互的中文报告，并支持基于报告追问；
- 克隆 GitHub 前必须经过 Human-in-the-loop 人工审批。

技术栈：

| 层 | 技术 |
| --- | --- |
| Agent / 后端 | Python 3.11+、LangChain 1.x、LangGraph 1.x、Pydantic 2 |
| 模型接入 | OpenAI 兼容协议，统一接入 DeepSeek / 智谱 GLM / OpenAI |
| Web 服务 | Python 标准库 `ThreadingHTTPServer`，无 FastAPI / Flask |
| 实时推送 | SSE（Server-Sent Events），分析事件与分析流共用事件总线 |
| 前端 | Vue 3、Vite 6、Less，无 UI 组件库 |
| 构建产物 | `static/dist/`，由 Python 服务托管 `/`、`/assets/*`、`/favicon.svg` |
| 持久化 | 报告 JSON 落盘 `data/reports/`；运行与对话记忆在内存 |

当前不依赖数据库、不依赖 Node 常驻服务、不需要登录。

---

## 2. 运行时拓扑

```text
Browser (Vue)
  │  GET /api/health, /api/examples, /api/history, /api/report
  │  POST /api/analyze  -> run_id
  │  GET  /api/events?run_id=...  (SSE)
  │  POST /api/hitl, /api/chat (SSE response)
  ▼
RepoLensHandler (stdlib ThreadingHTTPServer)
  ▼
RepoLensApp
  ├─ runs: dict[run_id, Run]        # 内存运行状态；超过 30 个时清理最旧完成项
  ├─ checkpointer: InMemorySaver    # 短期记忆 / LangGraph checkpoint
  └─ store: InMemoryStore           # 长期记忆 namespace=("repolens","analyses")
  ▼
analysis-<run_id> 后台线程
  ▼
run_analysis(ctx)
  ├─ build_analysis_agent(ctx)
  │    ├─ model = init_chat_model(OpenAI compatible)
  │    ├─ tools = 6 个 @tool
  │    └─ middleware = 进度 / 脱敏 / PII / 限流 / 重试 / Todo / HITL
  ├─ agent.stream(...) -> 事件
  ├─ AnalysisContext.emit -> EventBus -> SSE
  ├─ build_report(ctx, insight, ai_error)
  └─ save_report -> data/reports/<run_id>.json
```

### 2.1 线程模型

- HTTP 请求由 `ThreadingHTTPServer` 的工作线程处理（`daemon_threads=True`）。
- 每个分析在独立后台线程运行，线程名 `analysis-<run_id>`，daemon。
- 每个 Run 有自己的 `chat_lock`，避免同一个报告的多个追问并发改同一个 chat agent。
- `EventBus` 使用 `threading.Condition`，分析线程写、HTTP/SSE 线程读。
- 所有运行状态在进程内存；**进程重启后运行进度、短期对话记忆、长期记忆都会丢失**；报告 JSON 仍在磁盘。

---

## 3. 不可破坏的契约（先看这张表）

| 契约 | 定义位置 | 为什么不能随便改 |
| --- | --- | --- |
| 分析 API 响应字段 `run_id/source_type/model/ai_available` | `repolens/server.py` | 前端 `setupRun` 直接读取 |
| `GET /api/run` 字段 `status/report_ready/elapsed_seconds/repo_name/error` | `repolens/server.py` | 刷新恢复、历史打开依赖 |
| SSE 事件外层 `{seq,type,data,ts}` | `repolens/events.py`、`server.py` | 前端 `handleEvent` 按 `type` 分发 |
| 分析事件类型与字段 | 本文 §10 | `store.js` 的 UI 状态机直接依赖 |
| 报告 JSON 字段 | `repolens/report.py` | 报告页、导出、历史、追问都依赖 |
| 技术对象字段 | `scanner.TechHit.to_dict()` + `report.build_report()` | 技术卡片、抽屉、模块地图依赖 |
| HITL 决策只允许 `approve` / `reject` | `server._handle_hitl()` | 多一个值会导致 Agent 挂起或行为不确定 |
| 克隆被拒绝后立即结束 | `pipeline._run_agent()` | 防止模型反复重试被拒绝的工具 |
| 只读扫描、敏感文件拒绝 | `tools.py`、`security.py` | 安全承诺 |
| `static/dist` 可被 Python 直接托管 | `server.py`、`vite.config.js` | 只装 Python 的用户必须能运行 |
| 默认只监听 `127.0.0.1` | `config.py` | 项目没有登录鉴权 |

---

## 4. 代码地图

### 4.1 后端 / 根目录

| 路径 | 职责 | 关键符号 |
| --- | --- | --- |
| `run.py` | 启动入口，参数、版本检查、打开浏览器 | `main()`, `parse_args()` |
| `repolens/__init__.py` | 版本号 | `__version__ = "1.0.0"` |
| `repolens/config.py` | `.env` 加载、供应商选择、路径/端口/克隆限制 | `load_model_config()`, `ModelConfig`, `PROVIDERS` |
| `repolens/events.py` | 线程安全事件总线 | `EventBus.publish/snapshot/wait_for_new` |
| `repolens/context.py` | 一次分析的共享上下文 | `AnalysisContext.emit/progress/wait_for_decision` |
| `repolens/catalog.py` | 252 项技术词典、12 个分类、别名匹配 | `CATALOG`, `CATEGORIES`, `lookup()` |
| `repolens/scanner.py` | 纯 Python 扫描器：文件、语言、清单、import、技术聚合 | `scan_repository()`, `Snapshot`, `TechHit` |
| `repolens/schemas.py` | 结构化输出模型 | `RepoInsight`, `TechFinding`, `structured_output_error_handler` |
| `repolens/tools.py` | 6 个分析工具 | `build_tools()`, `repo_overview()` |
| `repolens/middleware.py` | 进度、脱敏、工具事件 | `ProgressMiddleware`, `SecretMaskingMiddleware` |
| `repolens/agent.py` | 模型、提示词、中间件、分析 Agent、追问 Agent | `build_analysis_agent()`, `build_chat_agent()` |
| `repolens/pipeline.py` | 分析主流程、Agent 循环、HITL、兜底、追问流 | `run_analysis()`, `_run_agent()`, `stream_chat()` |
| `repolens/report.py` | 事实 + AI 合并、报告持久化、历史摘要 | `build_report()`, `save_report()`, `list_reports()` |
| `repolens/sources.py` | 本地路径校验、GitHub 解析/克隆、体积检查 | `validate_local_path()`, `clone_github()` |
| `repolens/security.py` | 正则脱敏、敏感文件判断 | `mask_secrets()`, `is_sensitive_path()` |
| `repolens/server.py` | HTTP 路由、SSE、静态文件、运行管理、知识点文案 | `RepoLensApp`, `RepoLensHandler`, `create_server()` |

### 4.2 前端

| 路径 | 职责 |
| --- | --- |
| `frontend/vite.config.js` | Vue 插件、`@` 别名、Less 自动注入、构建到 `../static/dist`、`/api` 代理到 8765 |
| `frontend/index.html` | 单页挂载点 `#app`、favicon、默认深色 `data-theme` |
| `frontend/src/main.js` | 挂载 Vue、挂载前恢复主题、加载全局 Less |
| `frontend/src/App.vue` | 应用外壳、三视图切换、Header/Footer、抽屉/弹窗/Toast、全局快捷键 |
| `frontend/src/api.js` | `fetchJSON`、POST `/api/chat` 的 SSE 解析 |
| `frontend/src/store.js` | 单一响应式状态、所有业务动作、SSE 重连、URL 深链路 |
| `frontend/src/utils.js` | 分类颜色/图标、阶段、Tab、格式化、Markdown 导出、下载/复制 |
| `frontend/src/views/HomeView.vue` | 首页 hero、输入、示例、步骤/能力介绍、鼠标光晕 |
| `frontend/src/views/RunView.vue` | 分析页布局、状态胶囊、计时、错误/完成操作 |
| `frontend/src/views/ReportView.vue` | 报告头、统计、摘要、警告、Tab、分类筛选、搜索、技术卡片 |
| `frontend/src/components/StageTimeline.vue` | 四阶段时间线与进度 |
| `frontend/src/components/LiveFeed.vue` | 事件流筛选、自动滚动、过渡 |
| `frontend/src/components/TodoList.vue` | Agent 待办状态 |
| `frontend/src/components/TechCard.vue` | 技术卡片与置信度/模块/证据数 |
| `frontend/src/components/TechDrawer.vue` | 技术详情抽屉 |
| `frontend/src/components/ModuleMap.vue` | 模块地图、展开/收起、搜索、复制路径 |
| `frontend/src/components/ArchitectureTab.vue` | 架构、风险、学习路径、关键文件/目录/语言条 |
| `frontend/src/components/ChatTab.vue` | 追问、流式光标、推荐问题 |
| `frontend/src/components/ProcessTab.vue` | 当前会话事件回放与筛选 |
| `frontend/src/components/HistoryDrawer.vue` | 历史报告列表 |
| `frontend/src/components/ConceptsDrawer.vue` | 教程知识点手风琴 |
| `frontend/src/components/BaseDrawer.vue` | 抽屉基础组件 |
| `frontend/src/components/HitlModal.vue` | 克隆审批、倒计时圆环 |
| `frontend/src/components/AppHeader.vue` | 品牌、模型状态、历史、知识点、主题 |
| `frontend/src/components/ToastHost.vue` | 全局 Toast |
| `frontend/src/components/Icon.vue` / `BrandLogo.vue` | 内联 SVG 图标/品牌 |
| `frontend/src/styles/tokens.less` | 间距、圆角、字体、断点、颜色变量 |
| `frontend/src/styles/mixins.less` | `.panel()`、`.glass()`、`.mono()`、`.truncate()` 等 |
| `frontend/src/styles/global.less` | reset、主题变量、按钮/卡片/Tab/动画/滚动条 |

---

## 5. 后端调用链

### 5.1 启动

`run.py main()`：

1. 检查 Python ≥ 3.11（用到 `tomllib`）；
2. `config.load_model_config()` 读取 `.env` 并决定供应商；
3. `create_server(host, port)`：
   - 创建 `RepoLensApp`（checkpointer、store、报告目录）；
   - 从给定端口开始尝试最多 6 个端口；
4. 打印 URL，`--open` 时 1 秒后打开浏览器；
5. `serve_forever()`，Ctrl+C 关闭。

`.env` 加载顺序（`config.py`）：

1. `repolens/.env`；
2. 上一级目录 `.env`；
3. `override=False`，先加载者优先。

模型选择：

- `MODEL_PROVIDER` 明确指定则优先；
- 否则按 DeepSeek → GLM → OpenAI 找第一个有非占位 Key 的供应商；
- 都没有则返回 `available=False` 的配置，不抛异常；分析自动降级。

### 5.2 开始分析

`RepoLensApp.start_run(source)`：

1. 去空白、长度必须 ≤ 500；
2. `looks_like_github(source)` 判断来源：
   - GitHub：只做格式校验，真正克隆交给 Agent；
   - 本地：`validate_local_path()` 立即校验，失败立刻 400；
3. 加锁清理：最多同时 **2** 个 running；超过返回 `TooManyRuns`（HTTP 429）；
4. 运行数超过 30 时删除最旧的已完成运行；
5. 创建 `run_id = "<unix秒>-<8位hex>"`、`EventBus`、`AnalysisContext`；
6. 启动 daemon 线程 `analysis-<run_id>`，执行 `run_analysis(ctx)`；
7. 线程 finally 根据 `ctx.report` 设置 `run.status = done/error`。

### 5.3 `run_analysis` 阶段

```text
started
→ phase prepare（检查模型/环境）
→ 无 Key？ warning + 跳过 Agent
→ 有 Key：phase init → build_analysis_agent → _run_agent
→ Agent 未准备仓库？_fallback_scan（仅本地；GitHub 直接记录错误）
→ phase report → build_report → save_report
→ phase done + done 事件
→ ctx.finish() 关闭 bus
```

要点：

- `started` 事件包含 `run_id/source/source_type/model`。
- 没有 AI Key 时不会构建 Agent；本地仓库走纯规则扫描，仍可生成报告，并带 warning。
- GitHub 仓库依赖 Agent 的 clone 工具；没有 Key 时无法完成，最终 error。
- AI 构建/调用异常时记录 `ai_error`，仍尝试用已有 `ctx.snapshot` 生成规则报告。
- 报告保存失败会 emit `error` 并结束。

### 5.4 Agent 循环与 HITL

`_run_agent(agent, ctx)`：

- `recursion_limit = 250`；调用次数由中间件限制（模型 16 次、工具 40 次）。
- `for attempt in range(6)` 最多处理 6 次中断。
- 用 `agent.stream(payload, stream_mode=["updates","custom"])` 消费：
  - `updates`：识别 `__interrupt__`、todos、模型消息；
  - `custom`：工具内 `get_stream_writer()` 发来的进度。
- 出现 interrupt：
  1. `_wait_human_decision(ctx)` 阻塞等待 `decision_event`，超时 300 秒；
  2. 网页 `POST /api/hitl` → `ctx.submit_decision()`；
  3. `approve`：`Command(resume={"decisions":[{"type":"approve"}]})` 继续；
  4. `reject` 或超时：**立即设置 `ctx.error` 并 break**，不再重试被拒绝的克隆；
  5. 后续 `_fallback_scan` 对 GitHub 直接返回错误；`run_analysis` emit `error`。
- 非中断时正常结束循环；`agent.get_state()` 取 `structured_response`。

HITL 时序：

```text
Agent 调 clone_github_repository
→ HumanInTheLoopMiddleware 暂停
→ pipeline emit interrupt {action_requests, review_configs, id, timeout}
→ SSE → store.showHitl → HitlModal
→ 用户 approve/reject
→ POST /api/hitl
→ ctx.submit_decision → decision_event.set
→ pipeline resume / break
→ emit interrupt_resolved
→ UI 关闭弹窗并提示
```

关键文件：`agent.py`（HITL 中间件注册）、`pipeline.py`（决策循环）、`context.py`（线程等待）、`server.py`（HTTP 入口）。

### 5.5 追问

`server._handle_chat()`：

1. 校验 `run_id`（必填）和 `message`（非空、≤ 2000 字）；
2. 找运行；找不到但磁盘有报告 → `ensure_run_for_report()` 建一个已完成临时 Run；
3. 报告不存在 → 404/409；
4. 设置 SSE 响应头；
5. `with run.chat_lock:` 懒加载 `build_chat_agent(ctx)`；
6. `stream_chat(ctx, message, agent)` 逐条产出事件；
7. 前端 `streamChatRequest()` 解析。

`ensure_run_for_report` 的上下文：

- `bus` 创建后立即 close；
- `ctx.report` 来自磁盘；
- `source_note`、`local_path` 若仍存在则恢复 `repo_root`；
- 这样可以追问历史报告，但**跨进程的 LangGraph 短期记忆不会恢复**。

`stream_chat` 事件：

- `meta {model}`
- `token {text}`：只转发模型节点产生的 token
- `tool {name,args}`：模型计划调用报告工具时
- `done {ok:true}`
- `error {message}`

`config_ = {"configurable": {"thread_id": f"chat-{run_id}"}, "recursion_limit": 60}`。

---

## 6. 数据结构与报告格式

### 6.1 扫描数据结构

`Snapshot`（`scanner.py`）：

| 字段 | 说明 |
| --- | --- |
| `root` | 绝对路径 |
| `repo_name` | 根目录名 |
| `source`, `source_type` | 原始输入 / `local` 或 `github` |
| `files` | 相对路径列表（含被跳过内容的文件） |
| `file_count` | 文件数 |
| `code_file_count`, `total_loc` | 代码文件数 / 代码行数 |
| `size_bytes`, `truncated` | 体积 / 是否截断 |
| `languages` | `{name, files, loc, percent, is_code}` |
| `manifests` | 解析出的清单 |
| `techs` | `TechHit` 列表 |
| `top_dirs` | `{name, files}` 前 12 |
| `entry_points` | 入口/关键文件前 12 |
| `readme` | 根目录或一级 README 前 6000 字 |
| `scan_seconds` | 扫描耗时 |
| `omitted_dependencies` | 被省略的陌生依赖数 |

`TechHit`：

| 字段 | 说明 |
| --- | --- |
| `key` | 规范化小写 key |
| `name`, `category`, `hint` | 展示名、分类、说明 |
| `version` | 依赖版本，按“主依赖优先”评分选择 |
| `confidence` | `高/中/低`：语言/清单=高，import=中，AI 推断=低 |
| `sources` | `language` / `manifest` / `config` / `import` / `ai` |
| `evidence` | 最多 8 条 `{path,line,text,kind}` |
| `modules` | 最多 20 个 `{path,line,snippet,kind,role}`（按 path 去重） |

### 6.2 `RepoInsight` 结构化输出

`schemas.py` 要求模型按以下字段提交：

- `summary`：3–5 句中文摘要；
- `highlights`：2–5 条亮点；
- `architecture`：3–6 条分层说明；
- `techs`：`TechFinding[]`，每项 `name/category/role/key_modules/confidence`；
- `risks`：1–5 条风险/建议，可空；
- `learning_path`：3–6 步学习路线。

`category` 是 `Literal`，必须与 `catalog.CATEGORIES` 一致。结构化输出校验失败时，`structured_output_error_handler()` 返回中文纠错提示给模型重填。

### 6.3 最终报告 JSON

`build_report()` 输出（API 返回完整对象，磁盘保存同一结构）：

```json
{
  "run_id": "1730000000-abcd1234",
  "generated_at": "2026-10-25T00:00:00+08:00",
  "repo_name": "demo_shop",
  "source": "examples/demo_shop",
  "source_type": "local",
  "local_path": "C:/.../examples/demo_shop",
  "source_note": "本地目录",
  "summary": "...",
  "highlights": ["..."],
  "architecture": ["..."],
  "risks": ["..."],
  "learning_path": ["..."],
  "stats": {
    "file_count": 18,
    "code_file_count": 10,
    "total_loc": 165,
    "size_mb": 0.1,
    "truncated": false,
    "scan_seconds": 0.03,
    "omitted_dependencies": 0
  },
  "languages": [{"name": "Python", "files": 8, "loc": 120, "percent": 72.7, "is_code": true}],
  "manifests": [{"path": "requirements.txt", "kind": "requirements", "dependency_count": 5, "note": ""}],
  "top_dirs": [{"name": "backend", "files": 6}],
  "entry_points": ["backend/app/main.py"],
  "techs": [
    {
      "key": "fastapi",
      "name": "FastAPI",
      "category": "后端框架",
      "hint": "现代异步 Web 框架",
      "version": "0.115.6",
      "confidence": "高",
      "sources": ["manifest", "import"],
      "evidence": [{"path": "requirements.txt", "line": 3, "text": "fastapi==0.115.6", "kind": "依赖声明"}],
      "modules": [{"path": "backend/app/main.py", "line": 7, "snippet": "from fastapi import FastAPI", "kind": "导入", "role": "入口"}],
      "module_count": 1,
      "role": "在本仓库中提供 REST API...",
      "key_modules": ["backend/app/main.py"],
      "ai_inferred": false
    }
  ],
  "categories": [{"name": "后端框架", "icon": "🧱", "count": 3, "module_count": 5}],
  "warnings": [],
  "ai": {
    "used": true,
    "model": "智谱 GLM · glm-4.7",
    "error": null,
    "inferred_techs": [],
    "raw": []
  }
}
```

注意：

- `local_path` 是绝对路径，**只应留在本地 `data/`，不要放进公开仓库或截图**；
- `techs[].role/key_modules` 优先使用 AI 结果；AI 没给时用 `default_role()` 和扫描模块；
- AI 补充但扫描没找到的技术：`ai_inferred=true`、`confidence="低"`、`sources=["ai"]`，并写入 `warnings`；
- `warnings` 还可能包含：扫描截断、AI 失败、未使用 AI、AI 推断技术列表；
- 报告按分类顺序、置信度、模块数、名称排序。

### 6.4 持久化

- `config.REPORTS_DIR = data/reports/`；
- 文件名 `<run_id>.json`，`run_id` 必须匹配 `^[A-Za-z0-9_-]{1,80}$`；
- `save_report()` 写 UTF-8、缩进 2；
- `load_report()` 读失败/不存在返回 `None`；
- `list_reports(limit=40)` 只返回摘要：`run_id/repo_name/source/source_type/generated_at/tech_count/code_files/total_loc/ai_used`；
- `data/` 被 `.gitignore` 忽略。

---

## 7. 扫描器细节

### 7.1 上限与忽略

| 限制 | 值 |
| --- | --- |
| 文件数 | `MAX_FILES = 8000` |
| 读取内容的文件数 | `MAX_CONTENT_FILES = 2600` |
| 单文件读取 | `MAX_FILE_BYTES = 600_000` |
| 每项技术模块 | `MAX_MODULES_PER_TECH = 20` |
| 每项技术证据 | `MAX_EVIDENCE_PER_TECH = 8` |

`IGNORE_DIRS` 包括 `.git`、`node_modules`、`dist/build/out/target`、虚拟环境、缓存等；`.github` 等少数点目录允许。`IGNORE_FILENAMES` 包括各种 lock 文件。`IGNORE_SUFFIXES` 包括二进制、图片、媒体、模型权重等。

### 7.2 语言

`LANGUAGE_BY_SUFFIX` 覆盖 Python/JS/TS/Vue/Svelte/Java/Kotlin/Go/Rust/C/C++/C#/PHP/Ruby/Swift/Scala/Dart/Lua/Shell/PowerShell/SQL/HTML/CSS/SCSS/Less/Markdown/JSON/YAML/TOML/XML/Protobuf/HCL 等。

`is_code=False` 的语言（HTML/CSS/Markdown/JSON…）不进入代码行数统计，也不会作为编程语言技术项。

### 7.3 清单解析

支持：

- Python：`requirements*.txt`、`pyproject.toml`、`setup.py`、`setup.cfg`、`Pipfile`；
- JS：`package.json`；
- Java：`pom.xml`、`build.gradle(.kts)`；
- Go：`go.mod`；
- Rust：`Cargo.toml`；
- PHP：`composer.json`；
- Ruby：`Gemfile`；
- .NET：`*.csproj`；
- 容器/部署：`Dockerfile*`、`docker-compose*.yml`、`compose*.yml`；
- CI：`.github/workflows/*.yml`、`.gitlab-ci.yml`；
- IaC/服务：`*.tf`、Kubernetes YAML、`nginx.conf`、`Makefile`、`alembic.ini`、`.env.example`。

单个清单解析失败只记录 `note`，不会让整个扫描失败。

### 7.4 import 提取

正则覆盖 Python、JS/TS、Java/Kotlin、Go、Rust、Ruby、PHP、C/C++；Jupyter Notebook 会先抽取代码单元格再按 Python 解析。

匹配顺序：先查 `catalog.lookup(module)` 精确/别名/前缀；未知模块忽略，避免把标准库和第三方包误报。

### 7.5 技术聚合

1. 语言命中：代码语言 → `sources.add("language")`，置信度“高”；
2. 清单命中：依赖 → `sources.add("manifest")` 或配置类 `sources.add("config")`，置信度“高”；
3. import 命中：`sources.add("import")`，置信度至少“中”；
4. 未知依赖最多保留 24 个“其他依赖”，其余计入 `omitted_dependencies`；
5. 版本号按“主依赖 > 别名 > 其他”评分，只有更可信才覆盖；
6. 排序：分类顺序 → 置信度 → 模块数（多者前）→ 名称。

---

## 8. Agent 组装

### 8.1 分析 Agent 的工具

`tools.build_tools(ctx)` 用闭包绑定 `ctx`：

| 工具 | 作用 | 关键安全/行为 |
| --- | --- | --- |
| `clone_github_repository(url)` | 克隆公开 GitHub 仓库并扫描 | 唯一联网工具；HITL 必须批准；复用缓存；失败写 `ctx.error` |
| `inspect_local_repository(path)` | 扫描本地目录 | 只读；拒绝系统目录/磁盘根；可配置白名单 |
| `list_technologies(category="全部")` | 列出技术候选 | 不返回具体模块，控制 token |
| `inspect_technology(names)` | 查证据、import、模块路径 | 一次最多 8 个技术；每项证据前 5、模块前 10 |
| `read_project_file(relative_path, max_chars=1800)` | 读仓库内文本 | 拒绝敏感文件；路径穿越保护；限 400KB；脱敏；200–4000 字 |
| `remember_analysis(summary, runtime)` | 写入长期记忆 | namespace `("repolens","analyses")`，key=run_id |

`repo_overview()` 在扫描完成后返回给模型的概览包含：repo_name、root、note、stats、代码语言前 8、manifest 前 10、entry_points 前 8、top_dirs 前 8、tech_count、tech_preview 前 16、instructions。

### 8.2 中间件顺序

分析 Agent（`_common_middlewares()` + 追加）：

1. `ProgressMiddleware(ctx)`
2. `SecretMaskingMiddleware(ctx)`
3. `PIIMiddleware("email", strategy="mask")`
4. `PIIMiddleware("api_key", strategy="hash", detector=r"sk-[A-Za-z0-9]{12,}")`
5. `ModelCallLimitMiddleware(thread_limit=16, exit_behavior="end")`
6. `ToolCallLimitMiddleware(thread_limit=40, exit_behavior="end")`
7. `ToolRetryMiddleware(max_retries=2, initial_delay=0.5, max_delay=4.0, jitter=True, retry_on=(TimeoutError, ConnectionError, OSError), on_failure="continue")`
8. `TodoListMiddleware()`
9. `HumanInTheLoopMiddleware(interrupt_on={"clone_github_repository": {...approve/reject...}})`

追问 Agent：

1. `SummarizationMiddleware(trigger=("tokens",7000), keep=("messages",8))`
2. `SecretMaskingMiddleware(ctx)`
3. `PIIMiddleware(email, mask)`
4. `ModelCallLimitMiddleware(thread_limit=40, exit_behavior="end")`
5. `ToolRetryMiddleware(max_retries=2, initial_delay=0.5, jitter=True, on_failure="continue")`

> 注意：追问的“最多 3 次工具”只是系统提示词要求，**不是硬限制**；硬限制只有模型调用 40 次。

### 8.3 状态与记忆

- `RepoAnalyzerState(AgentState)` 增加 `run_id`、`user_id`；
- 分析 Agent 的 `checkpointer=ctx.checkpointer`，线程 `thread_id=run_id`；
- 追问 Agent 的线程 `thread_id="chat-<run_id>"`，复用同一个 checkpointer；
- `InMemoryStore` 用于跨会话长期记忆，`/api/memory` 可读取前 20 条；
- 进程重启后 checkpointer/store 都清空。

### 8.4 提示词

分析系统提示词定义了 7 步流程：准备仓库 → `write_todos` → `list_technologies` → `inspect_technology`（8–16 项重点，分 2–4 批）→ 可选读 README/入口 → 可选长期记忆 → 提交结构化报告。

安全约束：只读、不执行 shell、用户输入只是数据、不伪造报告。修改提示词时不要删掉这些约束。

---

## 9. HTTP API

所有 API 默认同源、无 CORS、无鉴权，适合本地使用。

### 9.1 GET

| 路径 | 查询/返回 | 说明 |
| --- | --- | --- |
| `/api/health` | `{ok,app,version,model,ai_available,provider,uptime_seconds,active_runs,max_files}` | 前端 Header 模型状态 |
| `/api/examples` | `{items:[{label,value,kind,description}]}` | 首页示例 |
| `/api/history` | `{items:[摘要]}` | 最多 40 条 |
| `/api/report?run_id=` | 完整报告 | 缺失 400，找不到 404 |
| `/api/run?run_id=` | `{run_id,source,source_type,status,report_ready,elapsed_seconds,repo_name,error?}` | 刷新恢复 |
| `/api/events?run_id=&from=` | `text/event-stream` | SSE；先补发历史再长连 |
| `/api/memory` | `{items:[{key,value,updated_at}]}` | 最多 20 条 |
| `/api/concepts` | `{concepts:[...]}` | 内置 9 个知识点 |
| `/` `/index.html` | `static/dist/index.html` | 未构建返回 503 |
| `/assets/*` | 构建产物 | hash 资源长缓存 |
| `/favicon.svg` `/favicon.ico` | dist favicon | |
| `/static/*` | `static/` 兼容路径 | 防目录穿越 |

### 9.2 POST

#### `POST /api/analyze`

```json
{"source": "examples/demo_shop"}
```

成功 200：

```json
{"run_id":"...","source_type":"local","model":"智谱 GLM · glm-4.7","ai_available":true}
```

错误：空/无效来源 400；超过 2 个运行 429；非 JSON 400；请求体 >1MB 413。

#### `POST /api/hitl`

```json
{"run_id":"...","decision":"approve|reject","message":"可选，最多 200 字"}
```

- 成功 `{"ok":true}`；
- `decision` 非枚举 400；
- run 不存在 404；
- 当前没有 `interrupt_payload` 409（例如已经决策或根本没暂停）；
- 拒绝后分析会立即结束（见 §5.4）。

#### `POST /api/chat`

```json
{"run_id":"...","message":"这个项目用了哪些数据库？"}
```

响应是 `text/event-stream`，每个事件：

```json
{"seq":1730000000123,"type":"token","data":{"text":"..."}}
```

限制：`run_id` 必填；`message` 非空、≤2000 字；同一 Run 的追问串行（`chat_lock`）。

### 9.3 通用错误

- 400：缺参数、来源非法、JSON 非法；
- 404：run/report/接口不存在；
- 409：HITL 无等待操作 / 报告未生成却追问；
- 413：请求体过大；
- 429：同时运行超过 2 个；
- 500：内部错误；
- 503：前端未构建。

---

## 10. SSE 事件契约

### 10.1 外层

分析事件（`GET /api/events`）统一为：

```json
{"seq":0,"type":"phase","data":{},"ts":1730000000.123}
```

- `seq` 从 0 单调递增；事件总线最多保留 4000 条，超限丢最旧但 seq 不回退；
- `ts` 是 Unix 秒（浮点）；
- 前端按 `seq <= lastSeq` 去重；断线由 `EventSource` 自动重连，服务端重发历史。

### 10.2 分析事件类型

| type | data（主要字段） | 前端行为 |
| --- | --- | --- |
| `started` | `run_id,source,source_type,model` | 更新模型、进入运行 |
| `phase` | `stage,label,duration?` | 更新阶段/时间线/状态文字 |
| `progress` | `message,percent?` | 实时进度行 |
| `tool` | `name,label,status(start/end/error),args,duration,preview,message` | 工具流 |
| `plan` | `tools:[{name,args}]` | “计划调用” |
| `todos` | `todos:[{content,status}]` | 待办清单 |
| `tokens` | `input,output,last_input,last_output` | Token 用量 |
| `meta` | `repo_name,root,note,stats,languages,manifests,entry_points,top_dirs,tech_count,tech_preview,instructions` | 扫描完成 |
| `model` | `status,call,message` | 模型开始/文本 |
| `assistant` | `content` | 截断展示 |
| `warning` | `message,hint?,detail?` | 警告 feed + Toast |
| `interrupt` | `action_requests,review_configs,id,timeout` | 打开 HITL |
| `interrupt_resolved` | `decision` | 关闭 HITL + Toast |
| `error` | `message,detail?` | 错误结束 |
| `done` | `run_id,repo_name,tech_count,ai_used,duration` | 完成并加载报告 |
| `log` | `message,level` | **当前前端未渲染**（已知限制） |

阶段映射（前端 `handleEvent`）：

- `prepare/init/fallback` → 阶段 0/1；
- `agent/reasoning/waiting_human/finishing` → 阶段 2；
- `report` → 阶段 3；
- `done` → 阶段 4。

### 10.3 追问事件

外层同样带 `seq/type/data`，但 `seq` 由毫秒时间戳生成，不是从 0 递增的序号；前端不使用它的去重逻辑。

| type | data | 说明 |
| --- | --- | --- |
| `meta` | `model` | 开始 |
| `token` | `text` | 增量文本 |
| `tool` | `name,args` | 报告工具调用提示 |
| `done` | `ok:true` | 结束 |
| `error` | `message` | 失败（无 Key、报告缺失、模型异常等） |

---

## 11. 前端实现

### 11.1 构建与托管

- `vite.config.js` 的 `build.outDir = "../static/dist"`，`emptyOutDir=true`，无 source map；
- `additionalData` 给每个 `<style lang="less">` 注入 `tokens.less` 和 `mixins.less`；
- `server.py` 用 `/assets/*` 映射 `static/dist/assets/*`；
- `/` 未构建时返回 503 + 提示；
- 生产构建产物已提交，所以 Python-only 环境无需 Node；
- 改前端后必须 `npm run build`，否则 8765 仍是旧 `dist`。

### 11.2 `store.js` 状态

核心字段：

| 字段 | 说明 |
| --- | --- |
| `view` | `home` / `run` / `report` |
| `health`, `examples` | 启动时并行拉取 |
| `source`, `analyzing` | 首页输入/请求中 |
| `run` | `{runId,source,sourceType,repoName,model,startedAt,status,error,stats?,techCount?}` |
| `report`, `reportLoading` | 报告 |
| `events`, `lastSeq`, `feed`, `feedFilter` | 事件回放/实时 feed |
| `todos`, `tokens`, `elapsed`, `stage` | 运行页 |
| `tab`, `category`, `search`, `pendingTab` | 报告筛选/深链路 |
| `chat` | `{messages,streaming,status}` |
| `drawers` | `{history,concepts,techKey}` |
| `history`, `concepts` | 抽屉数据 |
| `hitl`, `hitlRemaining`, `hitlPending` | 审批 |
| `toasts`, `theme`, `scrollProgress` | 全局 UI |

### 11.3 主要动作

| 动作 | 作用 |
| --- | --- |
| `initApp()` | 应用主题、拉 health/examples、解析 `?report/?run/?tab` |
| `startAnalysis(source)` | POST analyze → `setupRun` → EventSource |
| `setupRun()` | 清空上一次状态、设置 run、计时、SSE |
| `handleEvent()` | SSE 事件 → 状态机（核心） |
| `leaveRun()` | 运行中确认后进入后台，关闭 SSE/计时 |
| `loadReport(runId)` | 拉完整报告 → `showReport` |
| `showReport()` | 设置报告/阶段 4/Tab/URL；历史报告清空事件流 |
| `resumeRun(runId)` | 刷新后用 `/api/run` 恢复 |
| `switchTab(tab)` | 更新 tab + `?tab=` |
| `loadHistory()` / `loadHistoryReport()` | 历史列表/打开报告 |
| `sendChat()` | POST 流式追问，逐 token 更新 |
| `submitHitl()` | 提交 approve/reject |
| `exportJSON()` / `exportMarkdown()` / `copy()` | 导出/复制 |
| `applyTheme/toggleTheme` | localStorage `repolens-theme` |

### 11.4 URL 深链路

- `?run=<run_id>`：刷新/恢复运行或完成报告；
- `?report=<run_id>`：直接打开报告；
- `?report=<run_id>&tab=modules|architecture|chat|process`：打开指定 Tab；
- `switchTab` 用 `history.replaceState` 更新，不新增历史记录；
- 进入首页/离开运行会清空 query。

### 11.5 交互与可访问性

- 主题：默认深色，切换写入 `localStorage`；`main.js` 在挂载前恢复，减少闪烁；
- 键盘：首页 Enter 开始；报告技术栈页 `/` 聚焦搜索；`Esc` 关闭抽屉（HITL 弹窗必须显式选择，不允许 Esc 关闭）；
- 焦点：按钮/卡片有 `:focus-visible`/focus ring；
- 响应式：媒体查询 `@bp-md`/`@bp-lg`/`@bp-xl`；390px 已验证无横向溢出；
- 动画：页面/卡片/抽屉/Toast；`LiveFeed` 使用 `TransitionGroup`；
- 主题变量集中在 `tokens.less`/`global.less`，组件不要硬编码颜色。

---

## 12. 配置项

| 变量 | 默认 | 作用 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` / `GLM_API_KEY` / `OPENAI_API_KEY` | 空 | 至少一个才启用 AI |
| `MODEL_PROVIDER` | `auto` | 强制供应商 |
| `DEEPSEEK_MODEL` / `GLM_MODEL` / `OPENAI_MODEL` | 见 config | 模型名 |
| `*_BASE_URL` | 见 config | OpenAI 兼容地址 |
| `MODEL_TEMPERATURE` | 0.3 | 温度 |
| `MODEL_TIMEOUT` | 180 | 单次模型请求超时 |
| `REPOLENS_HOST` | `127.0.0.1` | 监听地址 |
| `REPOLENS_PORT` | `8765` | 端口；被占用自动 +1…+5 |
| `REPOLENS_ALLOWED_ROOTS` | 空 | 本地扫描白名单，逗号分隔；空=不限制 |
| `REPOLENS_MAX_CLONE_MB` | 300 | 克隆体积建议上限 |
| `REPOLENS_CLONE_TIMEOUT` | 180 | git clone 超时秒 |
| `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` | 空 | 可选 LangSmith |

`.env` 加载顺序见 §5.1。**不要提交 `.env`。**

---

## 13. 安全模型

### 13.1 只读与路径

- Agent 工具中没有写文件/执行 shell 的工具；
- `validate_local_path()`：必须存在、是目录；拒绝 `_FORBIDDEN_LOCAL` 中**精确匹配**的系统目录/磁盘根（如 `C:\Windows`、`C:\Users` 本身）；其子目录默认不在硬禁止列表，建议用白名单进一步限制；
- 可选 `REPOLENS_ALLOWED_ROOTS` 白名单；
- `read_project_file()` 用 `resolve() + relative_to(root)` 防目录穿越；
- 读取限制 400KB，返回前 200–4000 字。

### 13.2 GitHub 克隆

- 只支持公开 HTTPS GitHub；
- `git clone --depth 1 --single-branch --no-tags`；
- 超时 180s；体积超过 300MB 只警告，扫描仍受文件上限约束；
- 克隆前 HITL 必须批准；拒绝立即结束；
- 缓存目录 `data/repos/`，同一 URL 复用；不完整目录会清理重来。

### 13.3 敏感信息

`security.mask_secrets()` 处理：

- PEM 私钥块；
- `sk-...`；
- 32 位 hex + `.` + 8 位以上 GLM Key；
- `api_key/secret_key/access_key/... = value`；
- `password/passwd/pwd = value`；
- `token/authorization = value`；
- 数据库连接串中的密码。

`is_sensitive_path()` 拒绝：`.env`、`.env.local` 等（`.env.example/.sample/.template` 例外）、`id_rsa`、`id_ed25519`、`credentials*`、`secrets.yml/yaml`、`.pem/.key/.pfx/.p12/.jks/.keystore`。

`SecretMaskingMiddleware` 对所有工具返回内容再脱敏一次；`read_project_file` 自身也会脱敏。

### 13.4 Web

- 默认只监听 127.0.0.1；没有登录/权限系统，**不要随意绑定 0.0.0.0**；
- `_static()` 防目录穿越；
- CSP：`default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'`；
- `X-Content-Type-Options: nosniff`；
- 请求体上限 1MB；
- 来源长度 500、问题长度 2000、HITL message 200。

### 13.5 发布

- `.gitignore` 忽略 `.env*`、`data/`、`*.pem`、`*.key`、日志、`frontend/node_modules`、`docs/.chrome-*`；
- `check_secrets.py` 扫描项目，跳过本地 `.env` 内容，若 `.env` 被 Git 跟踪则失败；
- GitHub Actions `.github/workflows/secret-check.yml` 在 push/PR 运行；
- 截图可能含页面文字，扫描脚本无法识别，必须人工检查。

---

## 14. 开发、构建、验证

### 14.1 后端

```powershell
cd repolens
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run.py --open
```

语法检查：

```powershell
..\.venv\Scripts\python.exe -m compileall -q repolens
```

### 14.2 前端

```powershell
cd frontend
npm install
npm run dev      # 5173，/api 代理 8765
npm run build    # ../static/dist
```

只装 Python 时运行：

```powershell
python run.py
```

### 14.3 最小冒烟测试

```powershell
# 健康检查
Invoke-RestMethod http://127.0.0.1:8765/api/health

# 本地示例分析
$body = @{source="examples/demo_shop"} | ConvertTo-Json
$run = Invoke-RestMethod http://127.0.0.1:8765/api/analyze -Method Post -ContentType "application/json" -Body $body
$run.run_id

# 轮询
Invoke-RestMethod "http://127.0.0.1:8765/api/run?run_id=$($run.run_id)"

# 报告
Invoke-RestMethod "http://127.0.0.1:8765/api/report?run_id=$($run.run_id)"
```

### 14.4 发布前

```powershell
..\.venv\Scripts\python.exe check_secrets.py
git diff --cached --check
git status --short
```

---

## 15. 常见改动配方

### 15.1 新增一个 Agent 工具

1. 在 `tools.build_tools()` 内用 `@tool(parse_docstring=True)` 写函数；
2. docstring 必须写清用途、参数、何时使用；
3. 只读优先；有副作用必须加 HITL；
4. 错误用字符串返回，并写 `ctx.error`/`ctx.log`，不要静默吞掉；
5. 在 `middleware.TOOL_LABELS` 加中文名；
6. 更新 `ANALYZER_SYSTEM_PROMPT` 的流程；
7. 更新需求文档与本文工具表；
8. 跑一次真实本地分析 + 检查 SSE 工具事件。

### 15.2 新增 SSE 事件

1. 后端在合适的 `ctx.emit(...)` 发出；
2. 在 `frontend/src/store.js::handleEvent` 增加 `case`；
3. 在 `ProcessTab.describe()` 增加描述；
4. 更新本文事件表与需求文档；
5. 验证刷新补发时事件顺序/去重正常。

### 15.3 新增报告字段

1. `scanner`/`build_report` 产出字段；
2. 更新报告 JSON 文档；
3. 前端在 `ReportView`/对应 Tab 中渲染，缺省值要兼容旧报告（旧 JSON 没有新字段）；
4. 更新 `reportToMarkdown()`（如果需要导出）；
5. 更新需求文档的验收标准。

### 15.4 新增报告 Tab

1. `utils.TABS` 加 `{key,label}`；
2. `ReportView.vue` 加 `<section v-show="state.tab===...">`；
3. `store.switchTab` 的有效列表、URL `tab` 值；
4. 新建/复用组件；
5. 更新本文与需求文档。

### 15.5 改主题

1. 只改 `styles/tokens.less` 的浅/深变量；
2. 组件使用 `var(--...)`，不要硬编码；
3. 检查 `main.js` 的首屏主题；
4. 截图检查对比度。

### 15.6 改构建/托管

1. `vite.config.js` 的 `outDir`；
2. `server.py` 的 `DIST_DIR`、`/assets/*` 路由；
3. 构建并验证 `/`、`/assets/*`、`/favicon.svg`；
4. 保留“未构建 503”的友好提示。

---

## 16. 故障排查

| 现象 | 排查 |
| --- | --- |
| 页面 503：前端尚未构建 | `cd frontend && npm run build`，确认 `static/dist/index.html` |
| 首页显示“仅规则扫描” | 没有读到 API Key；检查 `.env` 位置/变量名/占位符 |
| 模型 401/404/超时 | Key 错 / 模型名错 / `MODEL_TIMEOUT` 太小；失败会降级规则报告 |
| 刷新后进度丢失 | 运行状态在内存；进程重启后无法恢复，报告仍在 `data/reports` |
| 追问历史报告没有上下文记忆 | 预期：`ensure_run_for_report` 只恢复报告，不恢复 checkpointer |
| 报告里技术模块为空 | 只在依赖清单/配置出现，没有直接 import；看 `evidence`/`hint` |
| GitHub 克隆失败 | 先确认命令行 `git clone` 可访问；公开仓库；代理/网络；GitHub 分析依赖 Agent |
| HITL 一直转圈 | 检查 `/api/hitl` 是否 409（没有 pending）；超时 300s 自动拒绝 |
| 前端改了但 8765 没变 | 没有 `npm run build`，或浏览器缓存了旧 index；强制刷新 |
| 5173 的 API 404 | Python 服务未启动；Vite 代理目标固定 8765 |
| 端口被占用 | `create_server` 自动尝试 +1…+5；看启动日志实际 URL |
| 事件流重复 | 前端按 `seq` 去重；检查服务端 `from`/seq |
| 报告里的 `local_path` 泄露 | 报告 JSON 只放 `data/`；不要提交/截图绝对路径 |

---

## 17. 已知限制与技术债

1. **没有自动化单元/端到端测试**；当前靠手动 QA 与 `check_secrets.py`。
2. **运行状态、事件、短期/长期记忆都在内存**；重启丢失。报告 JSON 落盘。
3. **没有鉴权**；默认 127.0.0.1，绑定公网需自行加反向代理/认证。
4. **SSE 使用 HTTP/1.0 短连接**，靠 `EventSource` 重连；没有 WebSocket。
5. **`log` 事件未在前端渲染**；UI 主要消费 `phase/progress/tool/warning`。
6. **追问工具次数是提示词约束**，没有 `ToolCallLimitMiddleware` 硬限制；只有模型调用 40 次上限。
7. **GitHub 分析依赖 Agent**：没有模型 Key 时无法克隆，不能只靠规则分析 GitHub。
8. **扫描是语法/正则级**：不构建 AST、不做跨文件类型推断；模块角色来自路径关键词。
9. **词典静态维护**（252 项）；未知依赖最多展示 24 个。
10. **报告文件历史无索引数据库**；每次 `/api/history` glob + 读 JSON，报告多时会变慢（当前上限 40 条展示）。
11. **HITL 只有克隆一个工具**；新增有副作用工具需要显式加入 `interrupt_on`。
12. **前端 CSS 使用 `color-mix` 等现代特性**；旧浏览器可能显示异常。
13. **没有实现 `prefers-reduced-motion` 的 CSS 降级**；动画在低性能设备上可能较重。
14. **`local_path` 绝对路径会写入本地报告**；公开分享报告时需删除/改用相对路径。
15. **`data/repos` 缓存不会自动清理**；长期使用需手动删除。

---

## 18. 修改前检查清单

- [ ] 已读 `REQUIREMENTS.md`，确认不会删除 P0 功能；
- [ ] 改动涉及 API/报告/事件字段时，前后端两处同步；
- [ ] 新增/修改工具时，docstring、错误处理、脱敏、HITL 都考虑；
- [ ] 前端改动后 `npm run build`，提交 `static/dist`；
- [ ] 本地示例完整跑通：首页 → 运行 → 报告 → 模块 → 架构 → 追问 → 历史；
- [ ] 检查 390px 移动端没有横向溢出；
- [ ] 检查 HITL approve/reject 路径；
- [ ] `check_secrets.py` 通过，`git diff --cached --check` 通过；
- [ ] 更新代码文档与需求文档；
- [ ] 不在公开文件/截图中出现 Key、本机用户名、真实 `local_path`。

---

## 19. 相关文档

- [需求文档](REQUIREMENTS.md)
- [项目 README](../README.md)
- [安全说明](../SECURITY.md)
- [Agent 入口](../AGENTS.md)
