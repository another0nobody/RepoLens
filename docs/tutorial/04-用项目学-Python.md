# 第 04 章：用项目学 Python

> 阅读时间：60–90 分钟  
> 前置：第 03 章  
> 目标：看懂这个项目里最常见的 Python 写法，而不是重新学一遍语法

---

## 4.1 这一章怎么用

你不需要先成为 Python 高手。  
本章只讲 RepoLens 真正用到的 Python 特性，并配项目中的真实例子。

顺序：

```text
包与导入 → 类型标注 → dataclass → Path → JSON
→ 异常 → 容器与推导式 → 函数/docstring
→ 线程 → 生成器 → 装饰器 → 读 traceback
```

每节都回答两个问题：

1. 这是什么？
2. 它在项目里用在哪？

---

## 4.2 包与导入

项目目录：

```text
repolens/
├── __init__.py
├── server.py
├── scanner.py
└── ...
```

`__init__.py` 让 `repolens/` 成为一个 Python 包。

因此可以写：

```python
from repolens.scanner import scan_repository
```

或者在包内部：

```python
from .scanner import scan_repository
```

`.` 表示“当前包”。

### 什么时候用绝对导入，什么时候用相对导入

- 包内部模块互相引用：常用相对导入 `from .scanner import ...`；
- 启动脚本、测试、外部调用：用绝对导入 `from repolens...`。

### 常见错误

```text
ModuleNotFoundError: No module named 'repolens'
```

原因通常是：

- 不在项目根目录运行；
- Python 路径没有包含项目根；
- 用了错误的虚拟环境。

---

## 4.3 类型标注：给数据写说明书

例子：

```python
def scan_repository(
    root: Path,
    source: str,
    source_type: str,
    progress: Progress = None,
) -> Snapshot:
    ...
```

含义：

```text
root 是 Path
source 是 str
source_type 是 str
返回值是 Snapshot
```

Python 运行时**不会强制检查**这些类型，它们是给人和编辑器看的。

好处：

- IDE 能自动补全；
- 读代码时知道数据形状；
- 减少“这个参数到底是字符串还是列表”的猜测。

### 常见写法

```python
str | None          # 字符串或 None
list[str]           # 字符串列表
dict[str, int]      # 键 str，值 int
set[str]            # 字符串集合
tuple[str, str]     # 两个字符串
Any                 # 暂时不限定类型
```

项目里大量使用 `from __future__ import annotations`，它让类型标注延迟求值，避免循环导入。

---

## 4.4 dataclass：有名字的数据包

扫描器的核心结果：

```python
@dataclass
class Snapshot:
    root: Path
    repo_name: str
    source: str
    source_type: str
    files: list[str]
    file_count: int
    code_file_count: int
    total_loc: int
    size_bytes: int
    truncated: bool
    languages: list[dict]
    manifests: list[Manifest]
    techs: list[TechHit]
    top_dirs: list[dict]
    entry_points: list[str]
    readme: str
    scan_seconds: float
    module_graph: dict = field(default_factory=dict)
```

`@dataclass` 自动生成：

- `__init__`；
- `__repr__`；
- 比较方法（默认按字段）。

你不需要写：

```python
def __init__(self, root, repo_name, ...):
    self.root = root
    ...
```

### 为什么用 dataclass

扫描结果字段很多，如果用普通 `dict`：

```python
snapshot["techs"]
snapshot["module_graph"]
```

拼错字段名运行时才发现。  
用 dataclass：

```python
snapshot.techs
snapshot.module_graph
```

编辑器能提示，读起来也更清楚。

### 技术记录 TechHit

```python
@dataclass
class TechHit:
    key: str
    name: str
    category: str
    hint: str
    version: str = ""
    confidence: str = "中"
    sources: set[str] = field(default_factory=set)
    evidence: list[dict] = field(default_factory=list)
    modules: dict[str, dict] = field(default_factory=dict)
    usage_tags: set[str] = field(default_factory=set)
```

这对应前端技术卡片：

```text
name / category / version / confidence
modules / evidence
```

`default_factory` 用于可变默认值。  
不要写：

```python
evidence: list = []
```

多个 `TechHit` 会共享同一个列表，产生隐藏 bug。  
项目用：

```python
field(default_factory=list)
```

每次创建新列表。

---

## 4.5 Path：比字符串更安全的路径

项目大量使用 `pathlib.Path`：

```python
from pathlib import Path

root = Path("examples/demo_shop").resolve()
for path in root.rglob("*"):
    if path.is_file():
        ...
```

对比字符串拼接：

```python
# 不推荐
path = root + "/" + name
```

`Path` 的好处：

- 自动处理 `/` 和 `\`；
- `.resolve()` 规范化 `..`；
- `.suffix`、`.name`、`.parent`；
- `.is_file()`、`.is_dir()`；
- `.read_text()`、`.stat()`。

### 路径安全

代码查看器必须确保文件在仓库根内：

```python
target = (root / relative_path).resolve()
if root not in target.parents and target != root:
    raise CodeViewError("只允许读取仓库内的文件", 403)
```

第 13 章会详细讲路径穿越。

---

## 4.6 JSON：前后端和报告的共同语言

读取 JSON：

```python
import json

data = json.loads(text)
```

写 JSON：

```python
json.dumps(data, ensure_ascii=False, indent=2)
```

- `ensure_ascii=False`：中文不转成 `\uXXXX`；
- `indent=2`：格式化，便于人看；
- 报告文件、API 响应、LLM 结构化输出都用 JSON。

### 常见错误

```text
json.decoder.JSONDecodeError
```

原因：

- 文件不是合法 JSON；
- 多了逗号；
- 用了单引号；
- 模型返回了 Markdown 代码块，不是纯 JSON。

项目里的结构化输出用 Pydantic 校验，避免直接把一段文本当 JSON。

---

## 4.7 异常：把失败变成可读信息

项目定义自己的异常：

```python
class SourceError(Exception):
    """来源有问题时抛出，消息会直接显示给用户。"""
```

工具里：

```python
try:
    path = validate_local_path(source)
except SourceError as exc:
    return {"error": str(exc)}
```

### 为什么不用 `return {"error": ...}` 到处传

- 异常能中断当前流程；
- 上层可以统一处理；
- 避免每一层都检查 `if error`；
- 但异常消息必须对用户可读。

### 常见异常类型

```text
ValueError        值不对
FileNotFoundError 文件不存在
PermissionError   没权限
TimeoutError      超时
KeyError          字典没有这个键
```

### 不要这样

```python
try:
    ...
except Exception:
    pass
```

这会吞掉错误。  
项目里确实有少量“不能影响主流程”的 `except Exception: pass`，比如事件持久化失败，但都有注释说明。

---

## 4.8 容器与推导式

### 字典：按 key 快速查找

```python
tech_by_key = {tech.key: tech for tech in techs}
```

### 集合：去重与成员判断

```python
seen = set()
if path in seen:
    continue
seen.add(path)
```

### 列表推导式

```python
names = [tech.name for tech in techs if tech.confidence == "高"]
```

等价于：

```python
names = []
for tech in techs:
    if tech.confidence == "高":
        names.append(tech.name)
```

推导式适合简单转换；复杂逻辑不要硬塞。

### 排序

```python
sorted(techs, key=lambda tech: len(tech.modules), reverse=True)
```

`key` 返回排序依据。  
项目用它按模块数、置信度、层级排序。

---

## 4.9 函数、默认参数与 docstring

```python
def read_code_window(
    repo_root,
    relative_path: str,
    line: int = 1,
    context: int = 8,
):
    ...
```

- `line` 默认 1；
- `context` 默认前后 8 行。

### 可变默认参数陷阱

不要：

```python
def add(item, items=[]):
    items.append(item)
```

列表会在多次调用间共享。  
用：

```python
def add(item, items=None):
    if items is None:
        items = []
```

### docstring

工具函数的 docstring 不只是注释。  
LangChain 的 `@tool(parse_docstring=True)` 会读取：

```python
@tool(parse_docstring=True)
def inspect_technology(name: str, runtime: ToolRuntime) -> dict:
    """查看某项技术的模块、证据和用途。

    Args:
        name: 技术名称，例如 Redis。
    """
```

模型通过函数名、参数说明、docstring 决定“该不该调用、怎么传参”。  
所以项目要求参数说明用中文，且写清楚。

---

## 4.10 线程：后台分析不阻塞网页

启动分析：

```python
threading.Thread(target=run_analysis, args=(ctx,), daemon=True).start()
```

- `target`：线程要执行的函数；
- `args`：参数元组；
- `daemon=True`：主进程退出时线程不阻止退出。

为什么需要线程？

- Agent 分析可能要几十秒；
- HTTP 请求不能一直挂着；
- 浏览器要实时看到进度。

### 线程安全事件总线

`EventBus` 用 `threading.Condition` 同步：

```python
with self._condition:
    self._events.append(event)
    self._condition.notify_all()
```

一个线程写，多个 HTTP 线程读。  
`Condition` 让读线程等待“有新事件”。

第 08 章会讲 SSE 如何消费它。

---

## 4.11 生成器：边生成边返回

追问流：

```python
def stream_chat(ctx, message, agent=None) -> Iterator[dict]:
    ...
    yield {"type": "token", "data": {"text": token}}
```

调用方：

```python
for event in stream_chat(ctx, message):
    ...
```

生成器不会等全部完成才返回，而是每次 `yield` 一个值。  
这正是“打字机效果”的基础。

### `yield` 和 `return` 的区别

- `return`：函数结束，返回一个值；
- `yield`：暂停函数，返回一个值，下次继续。

项目里：

```text
Agent 每产生一个 token
→ yield 一个事件
→ server 立即写入 SSE
→ 浏览器立即显示
```

---

## 4.12 装饰器：给函数加能力

```python
@tool(parse_docstring=True)
def list_technologies(...):
    ...
```

`@tool` 是 LangChain 的装饰器，把普通 Python 函数包装成 Agent 可调用的工具。

它做了：

- 读取函数名；
- 读取参数和 docstring；
- 生成工具 schema；
- 让模型知道如何调用。

项目里的工具都必须有清晰的：

```text
函数名
参数类型
参数说明
返回值
```

---

## 4.13 with：确保资源释放

```python
with self._condition:
    ...
```

`with` 会在代码块结束时自动释放/清理，即使中途异常。

其他例子：

```python
with open(path, encoding="utf-8") as f:
    text = f.read()
```

项目更常用 `Path.read_text()`，但语义一样。

---

## 4.14 读懂 traceback

看到：

```text
Traceback (most recent call last):
  File "pipeline.py", line 120, in run_analysis
    insight = _run_agent(agent, ctx)
  File "pipeline.py", line 150, in _run_agent
    for chunk in agent.stream(...):
  ...
  File "agent.py", line 95, in ...
TypeError: ...
```

读法：

1. 最下面：错误类型和信息；
2. 往上：调用栈；
3. 找**你写的文件**中最靠近底部的一行；
4. 看那一行的变量和参数。

不要只看第一行。

### 项目里的错误处理

`pipeline.run_analysis` 会捕获 Agent 异常：

```python
except Exception as exc:
    ai_error = f"{type(exc).__name__}: {exc}"
    ctx.emit("warning", {...})
```

然后降级为规则扫描。  
所以模型报错不一定让页面失败。

---

## 4.15 动手

### 练习 A：打印 Snapshot

在临时脚本里：

```python
from pathlib import Path
from repolens.scanner import scan_repository

snapshot = scan_repository(Path("examples/demo_shop"), "examples/demo_shop", "local")
print(snapshot.repo_name)
print(snapshot.file_count)
print([tech.name for tech in snapshot.techs])
print(snapshot.module_graph["stats"])
```

观察 `Snapshot` 的字段。

### 练习 B：读一个 JSON 报告

```python
import json
from pathlib import Path

data = json.loads(Path("data/reports/<run_id>.json").read_text(encoding="utf-8"))
print(data["schema_version"])
print(data["stats"])
```

### 练习 C：故意制造异常

把路径改成不存在：

```python
scan_repository(Path("does-not-exist"), "x", "local")
```

观察异常类型和信息。  
思考：工具层应该怎么把它变成用户可读的错误？

---

## 4.16 自测

1. `@dataclass` 帮你生成了什么？
2. 为什么可变默认值要用 `field(default_factory=list)`？
3. `Path.resolve()` 在安全上有什么用？
4. `yield` 和 `return` 的区别？
5. `@tool` 装饰器做了什么？
6. traceback 应该从哪一行开始看？

能回答后进入：[05 扫描器：把仓库变成事实](05-扫描器-把仓库变成事实.md)。
