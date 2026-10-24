# 敏感信息与发布安全检查

这个项目会读取代码仓库，并调用大模型 API，所以“不要把 Key 带进 Git”是第一条安全底线。
本文说明 RepoLens 已经做了哪些规避，以及你把它推到 GitHub 前应该检查什么。

---

## 1. 项目已经做的规避

### 1.1 密钥只在项目外

- 交付时 `repolens/` 项目目录内**不带 `.env`**；你可以在本地创建自己的 `.env`，但它已被 `.gitignore` 忽略；
- 运行时只会从以下位置读取配置：
  - 项目自己的 `.env`（如果你手动创建，已被 `.gitignore` 忽略）；
  - **上一级目录**的 `.env`（当前练习环境把 Key 放在这里）；
  - 操作系统环境变量。
- `/api/health` 只返回模型名和“是否配置”，**不返回 Key**；
- 服务端日志只打印请求行，不打印请求体，也不打印 Key。

### 1.2 `.gitignore` 的硬性规则

```gitignore
.env
.env.*
!.env.example
data/
*.pem
*.key
*.log
docs/.chrome-*/
frontend/node_modules/
```

其中 `data/` 保存克隆下来的仓库和生成的报告，属于运行时数据，不应该进入版本库。
**不要使用 `git add -f` 强行提交它们。**

### 1.3 截图已经处理

- `docs/` 中的报告截图使用 `examples/demo_shop` 作为来源，路径已改为相对路径；
- 不包含本机用户名或真实项目路径；示例输入中的 `C:\code\...` 是通用占位路径；
- 截图里只显示模型名（例如 `智谱 GLM · glm-4.7`），不显示 API Key。

> 如果你以后重新截图，请先确认地址栏、页面标题和报告来源里没有本机绝对路径。

### 1.4 运行时对敏感内容的处理

- `scanner` 会拒绝读取 `.env`、`id_rsa`、`*.pem` 等敏感文件；
- `read_project_file` 和 `SecretMaskingMiddleware` 会对 `sk-*`、密码、数据库 URL 等做脱敏；
- `PIIMiddleware` 会在消息进入模型前处理邮箱和 API Key；
- `data/reports/` 里的报告不会上传到模型服务商，只会由本地服务器读取。

### 1.5 演示数据不是真实凭据

`examples/demo_shop` 中的 `demo:demo` 数据库账号和密码是为了让示例可读而写的**假数据**，
不是任何真实环境的凭据。真实项目请使用环境变量或 Secret 管理。

---

## 2. 推送到 GitHub 前的检查清单

在项目目录下执行：

```powershell
# 1. 自动扫描真实 Key、常见 Key 格式和项目内 .env
python check_secrets.py

# 2. 初始化并暂存（如果还没有 Git 仓库）
git init
git add .
git status --short

# 3. 人工确认暂存区里没有 .env、data/、日志、临时截图目录
git status --short
```

期望结果：

- `check_secrets.py` 输出 `✅ 未发现 API Key / 私钥；项目内没有不应提交的 .env。`；
- `git status --short` 中没有 `.env`、`data/`、`*.log`、`docs/.chrome-*`；
- 如果你从整个工作区推送（而不是只推 `repolens/`），还要确认上一级的 `.env` 已被父级 `.gitignore` 忽略，并检查父目录下其他旧项目是否含有密钥。

> 建议只把 `repolens/` 作为一个独立仓库推送。这样 `.env`、`.venv`、`.pgdata` 和旧练习项目都不会被带进去。

仓库里还提供了 GitHub Actions 工作流：

```text
.github/workflows/secret-check.yml
```

每次 push / PR 都会自动运行 `python check_secrets.py`，作为第二道防线。

> 自动检查只能识别文本和常见格式。**图片里的文字无法识别**，截图仍需人工确认。

---

## 3. 如果 Key 已经泄露

1. **立刻去供应商控制台轮换/吊销 Key**（DeepSeek、智谱、OpenAI 等）；
2. 删除仓库中的 Key，并检查是否已经出现在 Git 历史中；
3. 仅删除最新一次 commit 不够，需要清理历史：
   - `git filter-repo`；
   - 或 BFG Repo-Cleaner；
4. 清理后强制推送，并通知协作者重新克隆；
5. 检查账单、调用日志和异常用量。

Key 一旦进入公开仓库，应该默认它已经泄露，轮换永远比“删掉文件”更重要。

---

## 4. 运行时的端口与访问范围

- Web 服务默认只监听 `127.0.0.1:8765`，不会暴露到局域网；
- 如果修改 `REPOLENS_HOST=0.0.0.0`，请自行增加认证、TLS 和防火墙规则；
- 本地路径扫描默认允许任意目录；可以用 `REPOLENS_ALLOWED_ROOTS` 限定范围。

---

如果你发现本项目有安全问题，请先不要公开提交 Issue，直接联系项目维护者并附上复现步骤。
