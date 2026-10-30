# AGENTS.md

> 给所有在本仓库工作的 AI Agent 的最短入口。
>
> 目标：**先恢复上下文，再改代码；不丢功能，不泄密，不破坏契约。**

---

## 0. 必读顺序

1. [需求文档](docs/REQUIREMENTS.md) — 功能契约、P0 清单、验收场景；
2. [代码文档](docs/CODE_DOCUMENTATION.md) — 文件地图、数据流、API/SSE/报告格式、已知限制；
3. [README](README.md) — 用户视角的安装、使用、教程映射；
4. 目标文件及相邻测试/组件 — 不要只凭文档假设实现。

如果文档与代码冲突：记录冲突，以当前代码行为为准，然后修正文档；不要为了“让文档成立”删除功能。

---

## 1. 项目地图（30 秒）

```text
repolens/
├── run.py                     # 启动入口
├── repolens/                  # Python 后端 + LangChain Agent
│   ├── server.py              # stdlib HTTP + SSE + 静态托管
│   ├── pipeline.py            # 分析主流程 + HITL + 追问流
│   ├── agent.py               # 模型/提示词/工具/中间件/结构化输出
│   ├── tools.py               # 6 个 Agent 工具
│   ├── scanner.py             # 确定性仓库扫描 + 模块依赖图
│   ├── catalog.py             # 252 项技术词典
│   ├── report.py              # 事实 + AI 合并、schema、落盘
│   ├── storage.py             # SQLite run/event/chat/report 索引
│   ├── diff.py                # 两份报告的差异计算
│   ├── sources.py             # 本地路径/GitHub 克隆
│   ├── security.py            # 脱敏/敏感文件
│   ├── schemas.py             # RepoInsight / TechFinding
│   ├── middleware.py           # Progress / SecretMasking
│   ├── events.py / context.py  # 事件总线 / 单次运行上下文
│   └── config.py              # .env、模型、端口、克隆限制
├── frontend/                  # Vue 3 + Vite + Less 源码
│   └── src/{views,components,store.js,api.js,theme.js,styles}
├── static/dist/               # 已提交的构建产物（Python 直接托管）
├── examples/demo_shop/        # 内置演示仓库
├── tests/                     # unittest 测试
├── docs/                      # 截图 + 本套文档
└── data/                      # 运行时报告/克隆缓存（gitignore）
```

---

## 2. 当前基线

- 后端版本：`1.0.0`
- 前端版本：`repolens-web@2.0.0`
- Python：3.11+
- Node：20+（只用于前端开发）
- 前端：Vue 3 + Vite 6 + Less，无 UI 库
- 后端：LangChain 1.x + LangGraph 1.x + Pydantic 2
- Web：Python 标准库，无 FastAPI/Flask
- 默认地址：`http://127.0.0.1:8765`
- 前端构建：`cd frontend && npm run build` → `static/dist`
- **只装 Python 也必须能运行**，因为 `static/dist` 已提交

---

## 3. 不能破坏的 P0（摘要）

完整清单见 [REQUIREMENTS.md](docs/REQUIREMENTS.md) 的 §8。

- 本地路径 + 公开 GitHub 两种来源；
- 只读扫描、敏感文件拒绝、路径穿越防护；
- GitHub 克隆必须 HITL 批准；拒绝后立即结束；
- 扫描器事实（文件/语言/清单/import/模块/行号/置信度/**文件大概功能**/**代码实际使用**：符号调用、连接串、用途标签）；
- 无 Key 的本地规则降级；AI 失败降级；
- 6 个工具 + 结构化输出 + 调用限制；
- 运行页实时时间线/待办/工具流/Token；
- 报告页技术卡/详情抽屉/模块地图/架构/风险/学习路径/警告；技术栈按**层级 → 功能 → 技术**分组（如“数据与存储 → 提供数据缓存 → Redis”），并支持“分组 / 层级图”切换；
- 历史、JSON/Markdown 导出、分享链接；
- **模块依赖图**：文件级本地 import 有向图，目录/文件视图、搜索、入边/出边、循环标记；
- **报告对比**：当前报告 vs 历史报告，技术/依赖/风险/架构/统计差异，排除纯职责文案噪声；
- 追问流式输出、报告依据、多轮记忆；**技术深挖四模板**（优势/难点/相似方案/为什么选它）+ `technology_deep_dive` 工具 + 事实/推断分离；
- **Contact Sheet 设计基线 × 深/浅模式**；
- 响应式、Toast、抽屉、HITL 弹窗；
- API/SSE/报告 JSON 字段契约；
- `static/dist` 静态托管；
- 安全扫描与不上传整仓。

删除/降级以上任何一项，必须有**人类明确批准**并同步更新文档。

---

## 4. 修改流程

1. **读**：需求文档 + 代码文档 + 目标文件；
2. **定位**：用代码地图找到后端/前端两侧受影响的位置；
3. **改**：小步修改，保持现有命名与契约；
4. **同步**：
   - API/SSE/报告字段 → 后端 + 前端 store/UI + 两份文档；
   - 新增工具 → `tools.py` + `TOOL_LABELS` + prompt + 需求文档；
   - 新增 Tab/组件 → `TABS` + `ReportView` + store 有效 tab + 深链接；
5. **构建**：前端改动必须 `npm run build` 并提交 `static/dist`；
6. **验证**：跑最小冒烟 + 相关验收场景；
7. **安全检查**：
   ```powershell
   ..\.venv\Scripts\python.exe check_secrets.py
   git diff --cached --check
   ```
8. **提交**：提交说明必须使用中文，写清改动与影响；不要提交 `.env`、`data/`、`node_modules`、截图 chrome profile。

---

## 5. 快速命令

```powershell
# 后端
cd repolens
python run.py --open

# 语法检查
..\.venv\Scripts\python.exe -m compileall -q repolens

# 前端开发
cd frontend
npm install
npm run dev      # 5173 -> /api 代理 8765

# 前端生产构建
npm run build    # ../static/dist

# 自动化测试
cd ..
..\.venv\Scripts\python.exe -m unittest discover -s tests -v

# 密钥扫描
cd ..
..\.venv\Scripts\python.exe check_secrets.py
```

最小 API 冒烟：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/health
$body = @{source="examples/demo_shop"} | ConvertTo-Json
$run = Invoke-RestMethod http://127.0.0.1:8765/api/analyze -Method Post -ContentType "application/json" -Body $body
Invoke-RestMethod "http://127.0.0.1:8765/api/run?run_id=$($run.run_id)"
Invoke-RestMethod "http://127.0.0.1:8765/api/report?run_id=$($run.run_id)"
```

---

## 6. 常见陷阱

- **只改源码不 build**：8765 仍加载旧 `static/dist`；
- **删 `static/dist`**：只装 Python 的用户会看到 503；
- **改 SSE 字段不同步**：运行页静默不更新；
- **改报告字段不同步**：旧报告可能崩溃/模板空白；
- **去掉 HITL**：违反安全承诺；
- **拒绝后继续 resume**：模型会反复重试克隆；
- **把 `local_path` 放进截图/公开文件**：泄露本机路径；
- **把 `.env` 或 `data/` 加入 Git**：泄露密钥/仓库内容；
- **在文档里承诺未实现功能**：先实现再写“已实现”；
- **以为追问工具次数有硬限制**：目前只有提示词约束，硬限制是模型 40 次；
- **改主题只改主色**：Contact Sheet 的深浅两套变量、字体、边框和印样纸色都要一起检查；
- **把深挖回答做成泛泛的技术百科**：必须先查报告和 `technology_deep_dive`，引用项目模块/行号，并明确区分事实、通用知识和推断；选型理由没有记录时不要编造；
- **删掉模块 `summary`**：模块地图/技术抽屉靠它显示“文件大概功能”；它是启发式摘要，但旧报告要保留前端 fallback；
- **只认 import/清单**：RedisCache、`redis.Redis(...)`、`redis://` 等代码使用会被漏掉；改动扫描器时保留 `detect_code_usages()` 和 `usage_tags`。

---

## 7. 验收清单（改完必看）

- [ ] `npm run build` 成功，`static/dist` 更新；
- [ ] `python -m unittest discover -s tests -v` 通过；
- [ ] 报告包含 `schema_version` 与 `module_graph`；SQLite `data/repolens.db` 可写入并重启恢复；
- [ ] `/api/diff` 与「对比历史」可用；同 run 400、缺失 404；
- [ ] `python run.py` 启动，`/` 与 `/assets/*` 200；
- [ ] 本地示例完整走通：首页 → 运行 → 报告 → 模块（每行有大概功能）→ 架构 → 追问（含技术深挖 4 模板）→ 历史；
- [ ] 无 Key 时本地规则报告仍可生成；
- [ ] HITL 批准/拒绝路径正确；拒绝立即结束；
- [ ] 390px 无横向溢出；Contact Sheet 深/浅主题正常且刷新保持；层级图窄屏为纵向树；
- [ ] `check_secrets.py` 通过；
- [ ] 没有提交 `.env`、`data/`、`node_modules`、`docs/.chrome-*`；
- [ ] 已更新需求文档/代码文档（如有契约变化）。
