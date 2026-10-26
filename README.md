# RepoLens · 代码仓技术栈侦探

> 输入一个本地代码仓路径或 GitHub 地址，得到一份看得懂、可核对、能追问的技术栈报告。
>
> 这是 **你的第一个 LangChain Agent 项目**：不要求你事先懂 Agent，README 会把用到的每个概念讲清楚。
>
> 前端：**Vue 3 + Vite + Less**，内置 **6 套页面风格 × 深/浅模式**；后端 / Agent：**Python + LangChain**。前端构建产物已提交，只装 Python 也能直接运行。

<details>
<summary><b>界面预览（点开看截图）</b></summary>

**首页：输入路径，一键开始**

![首页](docs/home.png)

**分析过程：时间线、待办清单、实时工具流**

![分析过程](docs/run.png)

**报告：技术栈全景 + 版本 / 置信度 / 职责**

![技术栈报告](docs/report.png)

**模块地图：精确到文件与行号**

![模块地图](docs/modules.png)

**架构解读：分层、风险与学习路径**

![架构解读](docs/architecture.png)

**追问：基于报告继续对话 + 技术深挖（流式输出 + 记忆）**

![追问](docs/chat-deep-dive.png)

**人工审批：克隆 GitHub 前必须由你确认**

![人工审批](docs/hitl.png)

> 截图使用内置示例仓库 `examples/demo_shop`；报告来源与运行页都使用相对路径，不包含本机用户名与真实项目路径。界面支持 6 套页面风格，每套都有深色 / 浅色模式。

</details>

---

## 项目文档

| 文档 | 给谁看 | 内容 |
| --- | --- | --- |
| [AGENTS.md](AGENTS.md) | AI Agent / 新维护者 | 最短上下文入口、P0 红线、修改流程、验收清单 |
| [需求文档](docs/REQUIREMENTS.md) | 产品 / 维护者 / Agent | 功能契约、优先级、状态机、验收场景、防遗忘清单 |
| [代码文档](docs/CODE_DOCUMENTATION.md) | 维护者 / Agent | 文件地图、调用链、报告 JSON、API/SSE 契约、前端 store、已知限制 |

> **给 Agent 的硬要求**：改代码前先读 [AGENTS.md](AGENTS.md) 和 [需求文档](docs/REQUIREMENTS.md)；任何 P0 功能删除都必须得到人类明确确认。

---

## 6 套页面风格

点击右上角「风格」即可切换。每套风格都会同时改变**配色、字体、背景纹理、卡片轮廓和光效**，不是简单换一个主色；深色 / 浅色可以独立切换，选择会保存在本地。

| 风格 | 关键词 | 适合 |
| --- | --- | --- |
| **极光 Aurora** | 深空蓝黑、青紫光晕、玻璃感 | 默认，长时间阅读报告 |
| **纸境 Paper** | 米白纸张、衬线标题、暖橙 | 技术刊物 / 文档感 |
| **终端 Terminal** | 磷光绿、等宽字体、扫描线 | 极客 / CLI / CRT |
| **霓虹 Neon** | 深紫夜色、青粉霓虹、强辉光 | 演示 / 展示 |
| **樱 Sakura** | 樱花粉、奶油白、柔光圆角 | 轻松 / 友好 |
| **晴空 Sky** | 蓝天、白云、阳光金 | 不想看科技风的时候；选择时自动切浅色 |

**新增：晴空 Sky（蓝天白云）**

![晴空风格](docs/style-sky.png)

![风格选择器](docs/style-picker.png)

<details>
<summary><b>展开 6 套完整首页截图</b></summary>

| 极光 | 纸境 | 终端 |
| --- | --- | --- |
| ![极光](docs/home.png) | ![纸境](docs/style-paper.png) | ![终端](docs/style-terminal.png) |
| **霓虹** | **樱** | **晴空** |
| ![霓虹](docs/style-neon.png) | ![樱](docs/style-sakura.png) | ![晴空](docs/style-sky.png) |

**纸境 · 浅色**：[查看截图](docs/style-paper-light.png)

**晴空 · 深色**：[查看截图](docs/style-sky-dark.png)

**移动端（晴空 · 浅色）**

<img src="docs/style-mobile.png" width="280" alt="移动端晴空浅色风格" />

</details>

---

## 1. 它能做什么

| 能力 | 说明 |
| --- | --- |
| 本地仓库分析 | 输入 `C:\code\my-project` 或 `./examples/demo_shop` |
| GitHub 仓库分析 | 输入 `https://github.com/owner/repo` 或简写 `owner/repo`，克隆前会弹窗让你批准 |
| 技术栈识别 | 依赖清单（requirements/pyproject/package.json/pom.xml/go.mod/Cargo.toml/compose/Dockerfile…）+ 源码 import 双路识别 |
| 模块级定位 | 精确到「哪个文件、哪一行、导入了什么」，并推测角色（接口层/数据模型/测试…）和**文件的大概功能**；代码里的符号调用/连接串也会补进技术栈 |
| 实时进度 | 扫描进度、工具调用、模型计划、Agent 待办清单、Token 用量全部实时推送 |
| AI 解读 | 项目摘要、架构分层、风险建议、学习路径；没有 API Key 时自动降级为纯规则报告 |
| 报告追问 | 基于报告继续问项目问题；针对任意技术可一键深挖「优势 / 难点易错点 / 相似方案差异 / 为什么选它」，带多轮记忆 |
| 人工审批（HITL） | Agent 克隆 GitHub 仓库前会真的暂停，等你在网页上点「允许」 |
| 历史与导出 | 报告保存在 `data/reports/`，支持历史列表、JSON / Markdown 导出、报告分享链接 |
| 页面风格 | 极光 / 纸境 / 终端 / 霓虹 / 樱 / 晴空，6 套视觉语言 × 深/浅模式，选择会被记住 |
| 安全 | 只读扫描、密钥脱敏、拒绝 `.env`/私钥、默认只监听 127.0.0.1 |

> 说明：报告里的「模块」来自**直接 import**（以及 Docker/Compose 等配置）。如果某个库只由框架间接使用，它可能显示「仅依赖声明，未找到直接 import」，这是正常的。

---

## 2. 快速开始

### 2.1 需要什么

- **Python 3.11+**（项目用到了标准库 `tomllib`）
- **Git**（只有分析 GitHub 仓库时需要；本地路径不需要）
- 一个大模型 API Key（三选一，不填也能用，只是没有 AI 解读）：
  - DeepSeek：<https://platform.deepseek.com/api_keys>
  - 智谱 GLM：<https://open.bigmodel.cn/usercenter/apikeys>
  - OpenAI
- 运行依赖：`langchain`、`langgraph`、`langchain-openai`、`pydantic`、`python-dotenv`
- **不需要 FastAPI / Flask**：网页服务器用的是 Python 标准库 `http.server`，下载即跑
- **Node.js 20+（可选）**：只有修改 Vue 前端源码时需要；项目已提交 `static/dist` 构建产物，平时运行只需要 Python

### 2.2 安装依赖

```powershell
cd repolens

# 方式 A：创建独立虚拟环境（推荐）
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 方式 B：复用本仓库上一级已有的练习环境
..\.venv\Scripts\python.exe run.py --open
```

如果你在 macOS / Linux：

```bash
cd repolens
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py --open
```

### 2.3 配置模型

```powershell
copy .env.example .env
notepad .env
```

至少填一个：

```dotenv
GLM_API_KEY=你的密钥
# 或者
DEEPSEEK_API_KEY=你的密钥
```

说明：

- 项目会**同时尝试读取** `repolens/.env` 和上一级目录的 `.env`（方便复用你已有的练习项目）；
- 不填任何 Key 也能启动：规则扫描仍然工作，页面会明确标注「仅规则扫描」；
- 智谱/DeepSeek 都走 OpenAI 兼容协议，所以代码里统一用 `langchain_openai`，不需要额外安装供应商包。

### 2.4 启动

```powershell
# 自动打开浏览器
python run.py --open

# 或者
.\start.ps1
.\start.bat
```

默认地址：<http://127.0.0.1:8765>。端口被占用时会自动往后找 5 个端口。

### 2.5 第一次体验

1. 打开页面，点击「内置示例仓库」→「开始分析」；
2. 观察左侧时间线、Agent 待办清单和右侧工具流；
3. 约 1~3 分钟后得到报告（取决于模型速度）；
4. 切到「追问」，问一句「这个项目用了哪些数据库和缓存？」；
5. 再试「这个项目自身」，或粘贴你本机的某个项目路径。

> 想看 GitHub 流程：输入 `psf/requests`。如果你的网络访问不了 GitHub，克隆会失败，页面会显示 git 的真实错误，不会卡住。

### 2.6 推送到 GitHub 前（重要）

这个项目已经针对“误传 API Key”做了几层规避：

- 项目交付时不带 `.env`；本地创建的 `.env` 已被 `.gitignore` 忽略，Key 只从本地配置或环境变量读取；
- `.gitignore` 忽略 `.env`、`.env.*`、`data/`、`*.pem`、`*.key`、日志和截图临时目录；
- `docs/` 报告截图已改为相对路径，不包含本机用户名与真实项目路径；
- 提供独立的密钥扫描脚本 `check_secrets.py`；
- 提供 GitHub Actions：每次 push / PR 自动运行扫描（`.github/workflows/secret-check.yml`）。

推送前建议执行：

```powershell
cd repolens
python check_secrets.py

git init
git add .
git status --short
```

确认暂存区里**没有** `.env`、`data/`、`*.log`、`docs/.chrome-*`，再提交、推送。
更完整的说明见 [SECURITY.md](SECURITY.md)。

> 注意：自动扫描无法识别图片里的文字。重新截图时，请确认页面中没有 Key、Token 或本机绝对路径。

### 2.7 前端开发（Vue 3 + Vite + Less）

日常运行 Python 不需要 Node.js。只有修改界面时才需要：

```powershell
cd frontend
npm install
npm run dev      # http://127.0.0.1:5173，/api 自动代理到 8765
```

开发完成后生成生产构建，交给 Python 静态服务器托管：

```powershell
npm run build    # 输出到 ../static/dist
```

然后刷新 <http://127.0.0.1:8765> 即可。Vite 配置在 `frontend/vite.config.js`：

- `@` 别名指向 `frontend/src`；
- 每个 `<style lang="less">` 自动注入 `tokens.less` 和 `mixins.less`；
- 生产构建输出到 `static/dist`，`index.html` 引用 `/assets/*`。

> `static/dist` 已提交，所以只装 Python 的机器也能直接运行；修改前端后记得重新 `npm run build` 并提交构建产物。

---

## 3. 界面怎么用

### 3.1 首页

- 输入框自动识别「本地路径」还是「GitHub 地址 / 相对路径」；
- 回车直接开始，也支持点击「开始分析」；
- 示例按钮只是帮你填入路径，不会自动开始；
- 右上角显示当前模型；没有配置 Key 时会显示「仅规则扫描」；
- 右上角「风格」可切换 6 套页面风格，右侧太阳/月亮切换深色与浅色；两项选择都会记住；晴空首次选择会自动切浅色。

### 3.2 运行页

| 区域 | 内容 | 来自哪个知识点 |
| --- | --- | --- |
| 时间线 | 检查环境 → 扫描仓库 → Agent 核实 → 生成报告 | 自定义 `ProgressMiddleware` |
| 待办清单 | Agent 自己拆解的步骤 | `TodoListMiddleware` |
| 工具流 | 每次工具调用的开始/结束/耗时/参数 | `wrap_tool_call` + `stream_mode="updates"` |
| 扫描进度 | 「已扫描 300 个文件…」 | 工具内 `get_stream_writer()` + `stream_mode="custom"` |
| Token 用量 | 输入/输出 token 累计 | `AIMessage.usage_metadata` |

如果 Agent 要克隆 GitHub 仓库，会弹出一个**必须选择**的审批框（允许/拒绝），5 分钟不选会自动拒绝。

### 3.3 报告页

- **技术栈**：按分类分组；除了依赖清单和 import，还会识别代码里的技术符号与连接串（如 `RedisCache`、`redis.Redis(...)`、`redis://`）；卡片显示用途、版本、置信度、职责、模块数、证据数；
- **模块地图**：按技术展开文件:行号、模块角色、**大概功能**、import 片段；支持全部展开 / 收起、复制路径、搜索；
- **架构解读**：摘要、亮点、架构分层、风险建议、学习路径、关键文件与目录规模；
- **追问**：多轮对话，有记忆；回答前会先查报告（工具调用），逐字流式输出；
- **技术深挖**：在追问页选择任意技术，或直接点四个模板——优势与场景、难点与易错点、相似方案差异、为什么选它；回答会区分项目事实和通用技术判断，并给出 2–3 个同类方案对比；
- **分析过程**：把本次 SSE 事件流按时间回放，可按「工具 / 阶段 / 异常」筛选；
- **导出**：JSON / Markdown；**分享链接**形如 `http://127.0.0.1:8765/?report=<run_id>`；
- **小交互**：技术卡片可点击查看详情、卡片与抽屉有过渡动画、顶部有阅读进度条、`/` 聚焦搜索框、`Esc` 关闭抽屉；
- **风格贯穿全站**：首页、运行页、报告页、抽屉、弹窗和 Toast 都会使用当前风格与深浅模式。

> 历史报告同样支持追问：服务器会从磁盘重建一个轻量上下文（见 `ensure_run_for_report`），但**跨进程的对话记忆不会保留**（短期记忆在 `InMemorySaver` 里）。

---

## 4. 它是怎么工作的

```text
浏览器
  │  POST /api/analyze {source}
  ▼
server.py ──────────────► 创建 Run、EventBus，启动后台线程
  │                              │
  │ GET /api/events (SSE)        ▼
  │                        pipeline.run_analysis
  │                              │
  │                              │ create_agent(model, tools, middleware, ...)
  │                              ▼
  │                        Agent 循环 ──► 工具：clone / inspect_local
  │                              │              │
  │                              │              ▼
  │                              │        scanner.py
  │                              │        精确扫描：语言、依赖、import、行号
  │                              │              │
  │                              │◄─────────────┘
  │                              │ 结构化输出 RepoInsight（Pydantic）
  │                              ▼
  │                        report.py 合并事实 + AI 解读
  │                              │
  │◄──── done + /api/report ─────┘ 保存 data/reports/<run_id>.json
  ▼
网页渲染报告
```

核心设计原则：

> **工具负责事实，模型负责解释。**

大模型读不完几千个文件，也可能看漏或编造；而「哪个文件第几行 import 了 fastapi」是可以精确数出来的。
所以 `scanner.py` 先产出硬事实，Agent 再基于这些事实归纳职责、架构和风险。
合并时以扫描结果为准：AI 多写的技术会被标成「AI 推断（无代码证据）」，漏写的技术会从扫描结果补回来。

---

## 5. 知识点详解（默认你没学过 Agent）

### 5.1 Agent 是什么？`create_agent` 做了什么？

普通调用大模型是「一问一答」。Agent 多了一个**循环**：

```text
用户问题 → 模型思考 → 要调工具吗？
                │ 是
                ▼
           执行工具 → 把结果还给模型 → 再思考 → …
                │ 否
                ▼
            最终回答
```

`create_agent(...)` 就是把这个循环（由 LangGraph 驱动）帮你搭好。你提供五样东西：

```python
agent = create_agent(
    model=model,                    # 用哪个大模型
    tools=tools,                    # 能调用哪些函数
    system_prompt=...,              # 角色 + 工作流程
    middleware=[...],               # 钩子：进度、审批、限流、脱敏…
    response_format=ToolStrategy(RepoInsight),  # 最终输出的格式
    state_schema=RepoAnalyzerState, # 自定义状态（多存一个 run_id）
    checkpointer=checkpointer,      # 短期记忆
    store=store,                    # 长期记忆
)
```

代码位置：`repolens/agent.py` 的 `build_analysis_agent()`。

**初学者常见误区**：以为 Agent 会「自动读文件」。不会。它只能调用你给的 Tool；没给的工具它一个也用不了。

---

### 5.2 Tool：Agent 的手和眼

Tool 就是「用 `@tool` 装饰的普通 Python 函数」。模型看到的不是函数源码，而是：

- 函数名；
- docstring（尤其是 `Args:` 里的参数说明）；
- 参数类型。

```python
@tool(parse_docstring=True)
def inspect_technology(names: list[str]) -> str:
    """查看一项或多项技术的详细证据……

    Args:
        names: 技术名称列表，例如 ["FastAPI", "SQLAlchemy"]
    """
    ...
```

`parse_docstring=True` 会解析 Google 风格的 `Args:`，生成更准确的参数 schema，降低模型传错参数的概率。

本项目 6 个工具（`repolens/tools.py`）：

| 工具 | 作用 | 是否联网/写盘 |
| --- | --- | --- |
| `clone_github_repository` | 克隆 GitHub 仓库到缓存目录 | 联网 + 写缓存（需审批） |
| `inspect_local_repository` | 校验并扫描本地目录 | 只读 |
| `list_technologies` | 列出技术候选 | 只读 |
| `inspect_technology` | 核实某几项技术的证据与模块 | 只读 |
| `read_project_file` | 读取仓库内文件片段 | 只读 + 脱敏 |
| `remember_analysis` | 写入长期记忆 | 写内存 Store |

**为什么工具要返回字符串？** 工具结果最终会作为 `ToolMessage` 交给模型，所以返回结构化 JSON 字符串或可读文本都可以。本项目尽量返回「短、密、可读」的文本/JSON，避免浪费上下文。

**ToolRuntime 是什么？** 某些工具需要访问 Agent 的运行时（当前状态、长期记忆 Store）。把参数标注成 `runtime: ToolRuntime`，LangChain 会自动注入，不需要模型传这个参数。见 `remember_analysis`。

---

### 5.3 结构化输出：让模型「填表」

网页需要稳定的字段，不能去解析一段中文作文。做法是给模型一个 Pydantic 模型：

```python
class RepoInsight(BaseModel):
    summary: str = Field(description="3~5 句中文概括……")
    techs: list[TechFinding] = Field(description="技术栈清单……")
    ...
```

然后：

```python
response_format=ToolStrategy(
    schema=RepoInsight,
    tool_message_content="分析报告已提交",
    handle_errors=structured_output_error_handler,
)
```

`ToolStrategy` 会偷偷给模型加一个「提交报告」的工具，参数 schema 就是 `RepoInsight`。
模型填错格式时，`handle_errors` 把错误翻译成中文提示返回给它重填，而不是让整个任务直接失败。

最终结果在 `agent.get_state(config).values["structured_response"]` 里（本项目在 `pipeline._run_agent` 取）。

**误区**：结构化输出不是「让模型输出 JSON 字符串再 `json.loads`」。`ToolStrategy` 走的是工具调用通道，校验更严格，也更容易重试。

---

### 5.4 流式输出：为什么页面能实时动

Agent 跑一次可能要几十秒。`agent.stream(...)` 会持续产出事件，本项目同时用了三种 `stream_mode`：

| 模式 | 内容 | 本项目用途 |
| --- | --- | --- |
| `updates` | 每个节点更新了什么 | 工具开始/结束、待办清单、中断 |
| `custom` | 工具内部 `get_stream_writer()` 主动发的消息 | 「已扫描 400 个文件…」 |
| `messages` | 模型逐 token 输出 | 追问页的打字机效果 |

工具里这样发进度：

```python
from langgraph.config import get_stream_writer

writer = get_stream_writer()
writer({"type": "progress", "message": "已扫描 400 个文件…"})
```

服务器把这些事件通过 **SSE**（Server-Sent Events，一种服务器单向推送的 HTTP 长连接）发给浏览器：

```text
data: {"seq":12,"type":"tool","data":{"name":"inspect_technology","status":"start",...}}

data: {"seq":13,"type":"progress","data":{"message":"已扫描 400 个文件…"}}
```

网页用 `EventSource` 接收，按 `seq` 去重（断线重连时服务器会重放历史事件）。

**误区**：SSE 不是 WebSocket。它更简单，只需要一个普通 GET 请求，浏览器会自动重连；缺点是只能服务器→浏览器单向。

---

### 5.5 中间件：不改 Agent 主流程，也能插入逻辑

中间件是「挂在节点上的钩子」。一次运行会经过：

```text
before_agent → before_model → [模型] → after_model → [工具] → before_model → … → after_agent
```

并且：

- 进入时按 `middleware=[A, B, C]` 的顺序执行 before；
- 返回时按 `C, B, A` 的顺序执行 after（像洋葱）；
- `wrap_tool_call` / `wrap_model_call` 可以「包住」一次调用，在前后都做事。

本项目用的中间件：

| 中间件 | 作用 | 教程 |
| --- | --- | --- |
| `TodoListMiddleware` | 给 Agent 加 `write_todos` 工具，拆解任务 | 第 8 章 |
| `HumanInTheLoopMiddleware` | 克隆前暂停，等人类批准 | 第 8 章 |
| `ModelCallLimitMiddleware` | 限制一次线程最多 16 次模型调用，防止死循环 | 第 8 章 |
| `ToolCallLimitMiddleware` | 限制工具调用总数 40 次 | 第 8 章 |
| `ToolRetryMiddleware` | 工具失败指数退避重试，`jitter=True` 防惊群 | 第 8 章 |
| `PIIMiddleware` | 邮箱 mask、API Key hash | 第 8 章 |
| `SummarizationMiddleware` | 追问对话过长时自动摘要 | 第 8/9 章 |
| `ProgressMiddleware`（自己写） | 把每个节点/工具变成网页事件 | 第 8 章自定义钩子 |
| `SecretMaskingMiddleware`（自己写） | 工具结果进模型前脱敏 | 第 8 章 wrap 钩子 |

自定义中间件长这样（`repolens/middleware.py`）：

```python
class ProgressMiddleware(AgentMiddleware):
    def before_model(self, state, runtime):
        self.ctx.emit("phase", {"stage": "reasoning", "label": "模型正在思考"})

    def wrap_tool_call(self, request, handler):
        self.ctx.emit("tool", {"name": request.tool_call["name"], "status": "start"})
        result = handler(request)
        self.ctx.emit("tool", {"name": request.tool_call["name"], "status": "end"})
        return result
```

**排序很重要**：`ProgressMiddleware` 放在 `SecretMaskingMiddleware` 外层，才能保证进度条里显示的是「已脱敏」的结果。

---

### 5.6 人机协同（Human-in-the-loop）：真的暂停

`HumanInTheLoopMiddleware` 会在模型决定调用某个工具后、工具真正执行前**中断**整个图：

```text
模型决定调用 clone_github_repository
        │
        ▼
  [中断] 状态写入 checkpointer
        │
        ▼
网页弹出审批框 ──批准──► Command(resume={"decisions":[{"type":"approve"}]})
        │
        └──拒绝──► Command(resume={"decisions":[{"type":"reject","message":"..."}]})
```

本项目在 `pipeline._run_agent` 里：

1. 用 `stream_mode=["updates","custom"]` 跑 Agent；
2. 收到 `__interrupt__` 事件 → 发 `interrupt` 给网页 → 阻塞等待 `ctx.decision_event`；
3. 网页 `POST /api/hitl` → 设置决策；
4. 用 `Command(resume=...)` 继续跑。

**注意**：中断不是「假装暂停」，`checkpointer` 会把完整状态存下来；即使进程重启（换成持久化 checkpointer），也能从断点恢复。

---

### 5.7 记忆：短期 vs 长期

| | 短期记忆 | 长期记忆 |
| --- | --- | --- |
| 组件 | `checkpointer`（本项目 `InMemorySaver`） | `store`（本项目 `InMemoryStore`） |
| 作用范围 | 同一个 `thread_id` 的对话历史 | 按 namespace + key 跨会话保存 |
| 本项目用途 | 追问多轮对话 | 保存每次分析的结论 |
| 生产替代 | `PostgresSaver` / `RedisSaver` | `PostgresStore` |

短期记忆：

```python
config = {"configurable": {"thread_id": f"chat-{run_id}"}}
agent.invoke({"messages": [HumanMessage("...")]}, config=config)
# 第二次 invoke 只传新消息，历史会从 checkpoint 里自动带出来
```

长期记忆（工具内）：

```python
@tool
def remember_analysis(summary: str, runtime: ToolRuntime) -> str:
    runtime.store.put(("repolens", "analyses"), run_id, {...})
```

注意：本项目为了「零外部依赖」，记忆都在进程内存里。**重启服务后短期记忆会消失**（历史报告仍在磁盘上，仍可追问，只是不带之前的聊天上下文）。

`SummarizationMiddleware` 用于追问：对话超过约 7000 token 时自动总结，只保留最近 8 条，避免上下文溢出。

---

### 5.8 自定义状态 `state_schema`

`AgentState` 默认只有 `messages`。本项目加了一个 `run_id`：

```python
class RepoAnalyzerState(AgentState):
    run_id: NotRequired[str]
```

这样工具里可以用 `runtime.state["run_id"]` 作为长期记忆的 key，而不需要模型去猜。

---

### 5.9 降级与安全

**降级**（`pipeline.run_analysis`）：

- 没有 API Key → 跳过 Agent，只用 `scanner.py` 生成报告；
- Agent 初始化失败/模型超时 → 捕获异常，仍然出规则报告；
- Agent 没调用扫描工具 → 后台兜底扫描一次；
- GitHub 没批准/网络失败 → 明确报错，不伪造报告。

**安全**：

- 只读扫描，不执行仓库里的任何代码；
- 拒绝系统目录、磁盘根目录；可用 `REPOLENS_ALLOWED_ROOTS` 限定范围；
- 拒绝读取 `.env`、`id_rsa`、`*.pem` 等敏感文件；
- 读取内容和工具结果都会做密钥脱敏（`sk-*`、password、数据库 URL 等）；
- 服务器默认只监听 `127.0.0.1`；
- 可选 `PIIMiddleware` 对输入中的邮箱/API Key 做 mask/hash；
- 发往模型的只有「必要的事实摘要 + 被读取的文件片段」，不会上传整个仓库。

**局限**（请如实看待报告）：

- import 扫描是静态的，动态导入（`importlib`、`require(variable)`）识别不到；
- 依赖清单里的传递依赖可能被当成直接依赖；
- AI 写的「职责」是解释性内容，可能有偏差；证据和模块路径才是硬事实；
- 没有一个通用工具能 100% 识别所有技术；遇到词典未收录的依赖会放入「其他依赖」。

---

## 6. 目录结构

```text
repolens/
├── run.py                    # 启动脚本（python run.py --open）
├── start.ps1 / start.bat     # Windows 一键启动
├── check_secrets.py          # 发布前密钥/敏感信息扫描
├── SECURITY.md               # 敏感信息与发布检查说明
├── AGENTS.md                 # AI Agent 最短入口（必读）
├── docs/
│   ├── REQUIREMENTS.md       # 需求契约 / P0 清单 / 验收场景
│   ├── CODE_DOCUMENTATION.md # 代码地图 / API / 数据流 / 限制
│   └── *.png                 # 界面截图
├── requirements.txt
├── .env.example              # 复制为 .env 填 Key
├── .github/workflows/        # CI：secret-check
├── frontend/                 # Vue 3 + Vite + Less 源码
│   ├── index.html
│   ├── vite.config.js        # 构建到 static/dist，dev 代理 /api
│   ├── package.json
│   ├── public/favicon.svg
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api.js / store.js / utils.js
│       ├── theme.js          # 6 套风格元数据、预览色、theme-color
│       ├── styles/           # tokens.less / mixins.less / global.less（风格变量）
│       ├── views/            # HomeView / RunView / ReportView
│       └── components/       # 头栏、时间线、技术卡片、风格选择器、抽屉、审批弹窗…
├── repolens/
│   ├── config.py             # 模型/端口/克隆限制配置
│   ├── events.py             # 进程内事件总线（线程安全）
│   ├── catalog.py            # 技术名词典（252 项，12 个分类）
│   ├── scanner.py            # 纯 Python 扫描器（不做 AI）
│   ├── sources.py            # 本地路径校验 / GitHub 克隆
│   ├── security.py           # 脱敏 / 敏感文件判断
│   ├── context.py            # 一次分析的共享上下文
│   ├── tools.py              # 6 个 Agent 工具
│   ├── middleware.py         # 2 个自定义中间件
│   ├── schemas.py            # 结构化输出 Pydantic 模型
│   ├── agent.py              # create_agent + 提示词 + 追问 Agent
│   ├── pipeline.py           # 编排：流式运行、HITL、降级
│   ├── report.py             # 事实 + AI 合并、持久化
│   └── server.py             # 标准库 HTTP 服务 + SSE API
├── static/dist/              # Vite 构建产物（已提交，Python 直接托管）
│   ├── index.html
│   ├── favicon.svg
│   └── assets/               # 带 hash 的 JS / CSS
├── examples/demo_shop/       # 自带演示仓库（FastAPI + React + Docker）
└── data/
    ├── repos/                # GitHub 克隆缓存（gitignore）
    └── reports/              # 生成的报告 JSON（gitignore）
```

### 建议的代码阅读顺序

第一次读这个项目，不要从 `scanner.py` 的 1400 行开始。建议按「请求怎么进来 → 怎么调用 Agent → 怎么扫描 → 怎么合并」的顺序：

1. `run.py`：入口，启动服务器；
2. `repolens/server.py`：HTTP 路由、SSE、`/api/analyze` 如何创建 Run；
3. `repolens/pipeline.py`：`run_analysis` 如何创建 Agent、转发事件、处理中断与降级；
4. `repolens/agent.py`：`create_agent` 的参数、系统提示词、中间件顺序、追问 Agent；
5. `repolens/tools.py`：6 个工具分别做什么、为什么这样写 docstring；
6. `repolens/scanner.py`：依赖清单和 import 是怎么被精确解析的；
7. `repolens/middleware.py`、`report.py`：进度事件如何产生、事实与 AI 如何合并；
8. `frontend/src/main.js` → `App.vue`：Vue 应用如何挂载、切换三个视图；
9. `frontend/src/store.js`：前端状态、SSE 重连、深链路、追问和 HITL 决策；
10. `frontend/src/views/` 与 `components/`：首页、运行页、报告页、风格选择器和各个交互组件；
11. `frontend/src/theme.js` 与 `styles/`：6 套风格的元数据、CSS 变量、字体、纹理和深浅模式。

---

## 7. 常用参数在哪调

| 想改什么 | 文件 | 参数 |
| --- | --- | --- |
| 换模型/温度/超时 | `.env` | `DEEPSEEK_*` / `GLM_*` / `MODEL_TEMPERATURE` / `MODEL_TIMEOUT` |
| 限制模型/工具调用次数 | `repolens/agent.py` | `ModelCallLimitMiddleware(thread_limit=16)` 等 |
| Agent 工作流程 | `repolens/agent.py` | `ANALYZER_SYSTEM_PROMPT` |
| 扫描文件上限 | `repolens/scanner.py` | `MAX_FILES = 8000` |
| 技术词典 | `repolens/catalog.py` | `CATALOG` 列表，照着格式加一行即可 |
| 克隆体积/超时 | `.env` | `REPOLENS_MAX_CLONE_MB` / `REPOLENS_CLONE_TIMEOUT` |
| 允许扫描的目录 | `.env` | `REPOLENS_ALLOWED_ROOTS` |
| HITL 等待时长 | `repolens/pipeline.py` | `HITL_TIMEOUT = 300` |
| 端口 | `.env` / 命令行 | `REPOLENS_PORT` / `--port` |
| 前端构建/代理 | `frontend/vite.config.js` | `build.outDir`、`server.proxy` |
| 前后端地址 | `frontend/src/api.js`、`store.js` | 全部使用相对路径 `/api/*` |
| 页面风格 | `frontend/src/theme.js`、`styles/global.less` | `STYLE_OPTIONS`、`[data-style]` 变量块 |
| 主题颜色/间距 | `frontend/src/styles/tokens.less`、`global.less` | CSS 变量与 Less 变量 |
| 记住的选择 | 浏览器 localStorage | `repolens-style` / `repolens-theme` |

### 给技术词典加一项

```python
T("Nuxt", "前端框架", ("nuxt", "nuxt3"), "基于 Vue 的全栈框架", "js"),
```

字段含义：展示名、分类、别名（依赖名/import 名/镜像名）、一句话说明、生态。

---

## 8. 常见问题

**Q：页面显示「仅规则扫描」，没有 AI 摘要？**
A：没有读到 API Key。检查 `.env` 是否在 `repolens/` 或上一级目录、变量名是否拼对；启动日志会打印当前模型。

**Q：模型报 401 / 404 / 超时？**
A：401 多半是 Key 错了；404 多半是模型名不对（例如 GLM 的可用模型名会变，见控制台）；超时把 `MODEL_TIMEOUT` 调大。本项目对失败会自动降级成规则报告。

**Q：运行 `pip install` 很慢 / 公司网络装不上？**
A：可以复用已有的 LangChain 环境（本项目只额外需要 `langchain-openai`、`python-dotenv`），或用国内镜像：
`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`。

**Q：改了前端界面但刷新页面没变化？**
A：前端是编译后由 Python 托管的。在 `frontend/` 执行 `npm run build`，生成新的 `static/dist` 后刷新。开发时可以用 `npm run dev`（5173）并让 Vite 代理 `/api` 到 8765。

**Q：`npm run dev` 打开 5173 后接口 404？**
A：先确认 Python 服务在 8765 运行；`vite.config.js` 已配置 `/api` 代理。生产模式直接用 8765 的 Python 服务即可。

**Q：GitHub 克隆失败？**
A：先确认 `git clone https://github.com/owner/repo` 在命令行能成功。公司网络可能需要代理：
`git config --global http.proxy http://127.0.0.1:7890`。私有仓库请先手动克隆到本地，再用本地路径分析。

**Q：为什么报告里有的技术「0 个模块」？**
A：它只出现在依赖清单、Docker 镜像或配置里，代码中没有直接 import。可能由框架间接使用（例如 `uvicorn` 由启动命令使用），也可能已废弃。点击技术卡片可以看到全部证据。

**Q：为什么扫描 8000 个文件就停了？**
A：防止误选超大目录耗尽内存。报告会标注「扫描已截断」。可以改 `scanner.MAX_FILES`，但建议先缩小到子目录。

**Q：报告存在哪？怎么清空？**
A：`data/reports/*.json`；直接删除即可。GitHub 克隆缓存在 `data/repos/`，也可删除。

**Q：端口被占用？**
A：`python run.py --port 9000`，或设置环境变量 `REPOLENS_PORT`。程序也会自动尝试后 5 个端口。

**Q：没有 `node_modules` / `.venv` 会不会影响识别？**
A：不会。扫描器默认跳过这些目录，避免把第三方依赖当成项目代码。

**Q：能不能分析私有仓库 / GitLab？**
A：私有仓库建议先 `git clone` 到本地，再输入本地路径。GitLab 需要改 `sources.py` 和 HITL 的工具名/URL 校验。

**Q：这个项目会把我的代码上传吗？**
A：不会上传整个仓库。发往模型的是扫描事实摘要、工具按需读取的文件片段（已脱敏）、以及报告生成所需的上下文。网页和扫描都在本机完成。

---

## 9. 可以继续做的练习

1. **把 `server.py` 换成 FastAPI**：练习路由、Pydantic 请求体、`StreamingResponse`；
2. **把记忆换成 PostgreSQL**：`PostgresSaver` + `PostgresStore`，实现重启后对话不丢（教程第 9 章）；
3. **加 RAG 技术知识库**：把技术文档切片入库，让 Agent 解释「这个框架通常怎么用」（教程第 10 章）；
4. **多 Agent 分工**：一个分析前端、一个分析后端、一个汇总（`create_agent` + 子图 / subagent）；
5. **接入更多生态**：Gradle、Bazel、GitLab CI、Kubernetes Helm values 的解析；
6. **继续扩展 Vue 前端**：加 Vue Router、组件库、报告对比 / diff、虚拟滚动；
7. **加依赖漏洞检测**：读取 lock 文件，对接 OSV 数据库；
8. **加 LangSmith 追踪**：在 `.env` 填 `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`，观察每一步的 token 与耗时（教程第 3 章）。

---

## 10. 与教程章节对照

| 教程章节 | 本项目中的落点 |
| --- | --- |
| 第 2 章 模型初始化 | `config.py` + `init_chat_model`（OpenAI 兼容协议统一三家） |
| 第 3 章 LangSmith | `.env` 可选开启追踪（不填不影响运行） |
| 第 4 章 Messages / Prompt | `HumanMessage`、`SystemMessage` 式系统提示词、`build_task_prompt` |
| 第 5 章 Tools | `@tool(parse_docstring=True)`、`ToolRuntime`、工具选择（6 个工具） |
| 第 6 章 结构化输出 | `schemas.py` 的 Pydantic 模型（ToolStrategy 底层复用） |
| 第 7 章 Agent | `create_agent`、系统提示词、`ToolStrategy`、`handle_errors`、`stream_mode` |
| 第 8 章 中间件 | `TodoListMiddleware`、`HumanInTheLoopMiddleware`、调用限制、重试、PII、`SummarizationMiddleware`、自定义钩子 |
| 第 9 章 记忆 | `InMemorySaver` + `thread_id`、`InMemoryStore` + `ToolRuntime`、摘要治理、`state_schema` |
| 第 10 章 RAG | 本项目的任务是「识别技术栈」，不依赖向量检索，所以没有强行使用；见「继续练习」第 3 条 |

---

## 11. 说明与许可

- 本项目是**学习项目**，用于演示 LangChain 1.x Agent 的常见能力，不是生产级代码扫描器；
- 技术识别基于静态扫描 + 模型归纳，**报告可能有遗漏或误判**；代码使用补充能抓住 `RedisCache`/`redis://` 等强信号，但动态拼接、反射和间接依赖仍可能漏，请以证据和源码为准；
- 扫描你自己的仓库前，请确认你拥有相应权限；
- 模型调用会产生费用，注意 `ModelCallLimitMiddleware` / `ToolCallLimitMiddleware` 的额度；
- 可自由用于学习、课程作业与二次开发。

---

如果这个项目帮你第一次跑通了 Agent，欢迎把它当成模板，换成你自己的工具和界面。
