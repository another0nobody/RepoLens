# 第 08 章：分析流水线、SSE 与 HITL

> 阅读时间：60–90 分钟
> 前置：第 06/07 章
> 目标：理解后台线程如何把 Agent 的每一步实时送到浏览器，以及失败时如何降级

---

## 8.1 一次分析为什么需要“流”

Agent 可能运行 30 秒到几分钟。
如果页面只显示一个 spinner：

- 用户不知道卡在哪；
- 不知道模型在做什么；
- 失败后不知道为什么；
- 长任务体验很差。

所以项目使用：

```text
Agent 每走一步
→ 产生事件
→ EventBus 保存/通知
→ HTTP SSE 推给浏览器
→ 运行页实时显示
```

---

## 8.2 pipeline 的职责

源码：`repolens/pipeline.py`。

`run_analysis(ctx)`：

```text
1. 发 started / phase
2. 检查模型配置
3. 有 Key：创建 Agent，跑 _run_agent
4. 无 Key/失败：降级扫描
5. 如果 snapshot 还没有：兜底扫描本地目录
6. build_report
7. save_report
8. 发 done / error
9. finish 事件总线
```

它不负责 HTTP，也不负责前端。

---

## 8.3 EventBus：事件总线

源码：`repolens/events.py`。

每个 run 一个：

```python
bus = EventBus(run_id, on_event=storage.append_event)
```

事件结构：

```python
{
    "seq": 0,
    "type": "phase",
    "data": {"stage": "scan", "label": "扫描仓库"},
    "ts": 1760000000.0,
}
```

`seq` 单调递增，用于：

- 断线重连从 `from=seq` 继续；
- 去重；
- 排序。

### 写入

```python
with self._condition:
    self._events.append(event)
    self._condition.notify_all()
```

### 读取

```python
bus.snapshot(from_seq)
bus.wait_for_new(from_seq, timeout=15)
```

### 关闭

```python
bus.close()
```

让所有等待中的 SSE 连接退出。

---

## 8.4 事件类型

常见事件：

| type | 含义 |
| --- | --- |
| `started` | 分析开始 |
| `phase` | 阶段变化 |
| `progress` | 扫描/工具进度 |
| `tool` | 工具调用；`data.status` 为 `start` / `end` / `error` |
| `plan` | 模型计划调用哪些工具 |
| `model` | 模型调用开始/文字输出 |
| `assistant` | 模型阶段性文字 |
| `tokens` | Token 用量 |
| `todos` | 待办清单 |
| `interrupt` | 等待 HITL |
| `interrupt_resolved` | 审批完成 |
| `warning` | 可恢复警告 |
| `error` | 失败 |
| `done` | 完成 |
| `meta` | 仓库概览 / 元信息 |

具体字段以 `events.py` 和前端 `LiveFeed` 为准。

---

## 8.5 SSE 是什么

SSE = Server-Sent Events。
服务器保持连接，持续推送文本：

```text
data: {"seq":0,"type":"phase","data":{...}}

data: {"seq":1,"type":"progress","data":{...}}

```

浏览器用 `EventSource` / `fetch` 读取。

项目用的是带 `data:` 前缀的 JSON：

```python
payload = json.dumps(event, ensure_ascii=False)
lines = [f"data: {line}" for line in payload.splitlines() or [""]]
chunk = "\n".join(lines) + "\n\n"
```

### 为什么不用 WebSocket

- SSE 单向（服务器→浏览器）足够；
- 标准库 HTTP 就能实现；
- 自动重连简单；
- 不需要额外协议。

### 为什么需要心跳

长时间无事件时，发送：

```text
: ping
```

防止代理/浏览器断开。

---

## 8.6 断线重连

前端保存最后收到的 `seq`。
重连时请求：

```text
GET /api/events?run_id=...&from=<last_seq>
```

`EventBus` 会：

- 先补发历史；
- 再等待新事件。

如果进程重启，内存事件没了，`server` 会从 SQLite 回放：

```python
persisted_events = storage.events(run_id, last_seq)
```

这就是为什么事件要持久化。

---

## 8.7 HITL 的完整流程

### 1. 模型请求克隆

```text
clone_github_repository(url=...)
```

### 2. 中间件中断

`HumanInTheLoopMiddleware` 让 Agent 暂停，产生 `__interrupt__`。

### 3. pipeline 推送

```text
event type = interrupt
data = {name, args, description, id, timeout}
```

### 4. 前端弹窗

用户点：

```text
允许 / 拒绝
```

前端：

```text
POST /api/hitl {run_id, decision}
```

### 5. 后端恢复

`pipeline` 阻塞在 `_wait_human_decision()`，收到 decision 后：

```python
Command(resume={"decisions": [decision]})
```

### 6. 拒绝

立即结束，不再重试同一个工具。

### 7. 超时

默认 300 秒，超时视作拒绝。

---

## 8.8 为什么拒绝后不能继续

如果模型被拒绝后继续尝试：

- 用户会被反复打扰；
- 可能绕过意图；
- 产生无意义 API 调用。

所以 pipeline 明确：

```python
if decision.get("type") != "approve":
    ctx.error = ...
    break
```

---

## 8.9 降级路径

### 没有 API Key

```text
ai_error = "没有配置..."
→ 不建 Agent
→ 规则扫描
→ build_report(insight=None)
```

### Agent 异常

```text
try build_agent/run
except:
  ai_error = ...
  → 规则扫描兜底
```

### Agent 没有准备仓库

```text
if ctx.snapshot is None:
    _fallback_scan(ctx)
```

### GitHub 没有准备好

- 如果是本地：再次扫描；
- 如果是 GitHub：设置错误，不远程重试。

### 报告仍然生成

```text
build_report(ctx, insight=None, ai_error=...)
```

前端显示：

```text
AI 解读失败 · 规则报告
```

---

## 8.10 追问流

`stream_chat(ctx, message)` 是生成器：

```text
meta
→ token（逐字）
→ tool（工具调用提示）
→ done
```

`server._handle_chat()` 把它写成 SSE。

### 历史恢复

进程重启后 checkpointer 为空，所以从 SQLite 聊天记录取最近 24 条：

```python
history = [...]
ctx.chat_seeded = True
```

这样多轮对话还能继续。

### 无 Key / 无报告

直接返回可读错误事件，不抛出 500。

---

## 8.11 错误处理的原则

1. 用户能看到发生了什么；
2. 能降级就降级；
3. 不能降级就明确失败；
4. 不把内部 traceback 直接丢给用户；
5. 日志保留 traceback 供开发者排查。

项目里：

- SSE `error` 事件给用户；
- 终端/日志保留异常；
- 报告里 `ai.error` 保留原因。

---

## 8.12 调试一次分析

### 看 `/api/run`

```text
GET /api/run?run_id=...
```

确认状态、是否报告 ready、错误。

### 看 `/api/events`

在浏览器 Network 里看 SSE 流。
如果没有事件，检查：

- run 是否创建成功；
- 后端是否在跑；
- 是否被代理缓冲。

### 看 `/api/report`

如果报告没生成，通常是：

- 扫描失败；
- 模型失败且兜底失败；
- run 还没结束。

### 看后端终端

`pipeline` 会打印异常 traceback。
这是第一手信息。

---

## 8.13 自测

1. 为什么 `/api/analyze` 立即返回，而不是等分析完成？
2. `seq` 有什么用？
3. SSE 断线后如何补事件？
4. HITL 的中断是在哪一层产生的？
5. 为什么拒绝后不能继续？
6. Agent 异常后，报告为什么还能生成？
7. 追问历史在进程重启后如何恢复？

能回答后进入：[09 报告数据模型与可核对功能](09-报告数据模型与可核对功能.md)。
