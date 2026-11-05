# RepoLens 评测 Harness

评测只跑确定性扫描器，不调用模型，不消耗 API Key。目标是防止“修一个仓库，弄坏另一个仓库”。

## 快速运行

```powershell
# 全部用例
..\.venv\Scripts\python.exe scripts\evaluate.py --out evals/latest.json --md evals/latest.md

# 单个用例
..\.venv\Scripts\python.exe scripts\evaluate.py --case node_api
```

退出码：

- `0`：所有用例通过；
- `1`：有用例失败；
- `2`：用例文件或参数错误。

## 当前用例

| id | 路径 | 覆盖生态 |
| --- | --- | --- |
| `demo_shop` | `examples/demo_shop` | Python / FastAPI / React / PostgreSQL / Redis / Docker |
| `node_api` | `evals/fixtures/node_api` | JavaScript / Express / Vitest |
| `go_service` | `evals/fixtures/go_service` | Go / Gin / Docker |
| `rust_cli` | `evals/fixtures/rust_cli` | Rust / serde |

## 指标

- **技术召回**：期望技术中扫描到的比例；必须为 1.0 才通过；
- **证据覆盖**：带证据或模块的技术占比；
- **语言**、**入口文件**：期望值必须全部命中；
- **文件数 / LOC**：防止扫描器静默漏扫；
- **依赖图节点/边**：防止模块依赖图退化；
- **extra_techs**：扫描器额外识别的技术，只记录，不直接判失败。

## 增加一个仓库

1. 把仓库放进 `evals/fixtures/<id>`，或使用任意本地路径；
2. 在 `evals/cases.json` 加一个 case；
3. 至少写 `techs`、`languages`、`entry_points` 和 `min_files`；
4. 运行单用例，确认期望是真实扫描结果而不是猜的；
5. 提交用例与夹具，不提交 `latest.json/latest.md`。

```json
{
  "id": "my_repo",
  "path": "evals/fixtures/my_repo",
  "expected": {
    "techs": ["Python", "FastAPI"],
    "languages": ["Python"],
    "entry_points": ["app/main.py"],
    "min_files": 3,
    "min_loc": 10,
    "min_graph_nodes": 1,
    "min_graph_edges": 0,
    "min_evidence_ratio": 0.8
  }
}
```
