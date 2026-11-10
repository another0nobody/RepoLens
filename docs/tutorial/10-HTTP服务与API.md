# 第 10 章：HTTP 服务与 API

> 阅读时间：45–60 分钟
> 前置：第 03/08 章
> 目标：理解标准库 HTTP 服务如何承载分析、报告、SSE 和静态页面

---

## 10.1 为什么用标准库

项目没有使用 FastAPI/Flask，而是：

```text
http.server.ThreadingHTTPServer
BaseHTTPRequestHandler
```

原因：

- 只装 Python 就能运行；
- 依赖已经够多（LangChain），少一个 Web 框架；
- 本地单机工具，路由不复杂；
- 便于学习者理解 HTTP 底层。

代价：

- 需要自己写路由、JSON、SSE、静态文件；
- 没有自动参数校验；
- 需要自己处理线程/错误。

---

## 10.2 服务器入口

```text
run.py
→ create_server(host, port)
→ RepoLensHTTPServer(ThreadingHTTPServer)
→ 绑定 app
→ serve_forever()
```

`create_server` 会尝试端口回退：

```text
8765 → 8766 → ... → 8770
```

所以看终端实际打印的 URL。

---

## 10.3 RepoLensApp 与 Handler

- `RepoLensApp`：业务状态；
- `RepoLensHandler`：HTTP 细节。

`RepoLensApp`：

```text
runs: dict[run_id, Run]
storage: SQLiteStore
lock
checkpointer / store
start_run / get_run / get_report / history / health
```

`Run`：

```text
run_id / source / source_type
ctx / thread / status
chat_agent / chat_lock
```

Handler 不直接扫文件，只调用 `app` 和 `pipeline`。

---

## 10.4 路由表

### GET

| 路径 | 作用 |
| --- | --- |
| `/` | 前端页面 |
| `/assets/*` | Vite 构建产物 |
| `/favicon.svg` | 图标 |
| `/api/health` | 服务/模型状态 |
| `/api/examples` | 示例仓库 |
| `/api/history` | 历史报告 |
| `/api/diff?base=&target=` | 报告差异 |
| `/api/file?run_id=&path=&line=` | 证据代码窗口 |
| `/api/adr?run_id=&tech=` | ADR Markdown |
| `/api/risks?run_id=` | 风险面板 |
| `/api/report?run_id=` | 完整报告 |
| `/api/run?run_id=` | 运行状态 |
| `/api/events?run_id=&from=` | SSE 事件流 |
| `/api/chat/history?run_id=` | 追问历史 |
| `/api/memory` | 长期记忆 |
| `/api/concepts` | 知识点文案 |

### POST

| 路径 | 作用 |
| --- | --- |
| `/api/analyze` | 开始分析 |
| `/api/hitl` | 批准/拒绝克隆 |
| `/api/chat` | 追问（SSE 流） |
| `/api/ground` | 引用核对 |
| `/api/ground/semantic` | 语义深度核对 |

---

## 10.5 一次 POST /api/analyze

请求：

```json
{"source": "examples/demo_shop"}
```

处理：

```python
source = payload["source"]
run = app.start_run(source)   # 校验 + 创建 run + 启动线程
return {
  "run_id": run.run_id,
  "source_type": run.source_type,
  "model": cfg.display_name,
  "ai_available": cfg.available
}
```

`start_run` 会：

- 校验来源；
- 判断 GitHub/本地；
- 限制并发 `MAX_ACTIVE_RUNS = 2`；
- 清理旧运行；
- 创建 `EventBus`；
- 创建 `AnalysisContext`；
- 启动 daemon 线程。

---

## 10.6 JSON 响应

统一：

```python
self._json(payload, status=200)
```

会设置：

```text
Content-Type: application/json; charset=utf-8
Content-Length
```

错误响应通常是：

```json
{"error": "可读的中文原因"}
```

前端 `fetchJSON` 会把它转成异常。

---

## 10.7 SSE 响应

`/api/events`：

```text
Content-Type: text/event-stream; charset=utf-8
Cache-Control: no-cache, no-transform
Connection: close
X-Accel-Buffering: no
```

发送：

```text
data: {"seq":...}

```

心跳：

```text
: ping

```

如果 run 不在内存：

- 从 SQLite 读事件回放；
- 没有事件则 404。

---

## 10.8 静态文件

```text
/            → static/dist/index.html
/assets/x.js → static/dist/assets/x.js
/favicon.svg → static/dist/favicon.svg
```

安全：

- 只允许 `dist` 内；
- 不暴露项目源码；
- 缺失 `static/dist` 返回 503，并提示构建。

---

## 10.9 错误码约定

| 状态 | 含义 |
| --- | --- |
| 400 | 参数缺失/非法 |
| 403 | 路径越界、敏感文件 |
| 404 | 报告/运行/文件不存在 |
| 409 | 同一 run 的追问正在进行，或报告未就绪 |
| 413 | 请求体/文件太大 |
| 415 | 二进制文件 |
| 429 | 同时分析任务过多 |
| 500 | 服务器内部错误 |
| 502 | 模型返回无法解析/上游失败 |
| 503 | 无模型/静态资源缺失 |

---

## 10.10 追问为什么用 POST + SSE

请求体可能较长（问题、run_id），用 POST 更自然。
响应需要逐字流式输出，所以：

```text
POST /api/chat
Accept: text/event-stream
```

前端 `api.js` 用 `fetch` + `ReadableStream` 手动解析 SSE。

---

## 10.11 并发与锁

- 每个 run 一个后台线程；
- 最多 2 个 active run；
- 同一 run 的追问用 `chat_lock` 串行；
- `SQLiteStore` 处理线程安全；
- `EventBus` 用 `Condition`。

为什么限制：

- 本地 CPU/API 配额；
- 避免一次点 10 个分析。

---

## 10.12 增加一个 API 的步骤

1. 在 `do_GET` / `do_POST` 加分支；
2. 写 `_handle_xxx`；
3. 校验参数；
4. 返回 `_json`；
5. 错误码明确；
6. 前端 `api.js` 增加函数；
7. 文档/需求更新；
8. 测试。

示例：

```python
elif path == "/api/example":
    self._handle_example(parsed)
```

不要在 Handler 里写复杂业务；放到 `app` 或独立模块。

---

## 10.13 手动调试

```powershell
# 健康
curl http://127.0.0.1:8765/api/health

# 开始分析
curl -X POST http://127.0.0.1:8765/api/analyze `
  -H "Content-Type: application/json" `
  -d '{"source":"examples/demo_shop"}'

# 读取报告
curl "http://127.0.0.1:8765/api/report?run_id=..."

# 风险
curl "http://127.0.0.1:8765/api/risks?run_id=..."

# 代码窗口
curl "http://127.0.0.1:8765/api/file?run_id=...&path=backend/app/main.py&line=10"
```

PowerShell 的 `curl` 可能是 `Invoke-WebRequest` 别名，必要时用 `curl.exe`。

---

## 10.14 自测

1. 为什么项目不用 FastAPI？
2. `/api/analyze` 返回时分析完成了吗？
3. `/api/events` 断线后如何补事件？
4. `MAX_ACTIVE_RUNS` 是多少？
5. 403、404、409、429 分别代表什么？
6. 为什么追问用 POST + SSE？
7. 静态文件为什么只托管 `dist`？

能回答后进入：[11 前端 Vue 与交互](11-前端Vue与交互.md)。
