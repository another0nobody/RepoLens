# Demo Shop（RepoLens 演示仓库）

这是一个用于演示 **RepoLens 技术栈分析** 的小型商城项目：后端提供订单接口，
前端展示订单列表，数据库和缓存用 Docker Compose 编排。

## 结构

- `backend/`：FastAPI + SQLAlchemy + PostgreSQL + Redis，接口在 `backend/app/api/routes.py`
- `frontend/`：React + TypeScript + Vite + Tailwind CSS + Axios
- `docker-compose.yml`：PostgreSQL、Redis、后端、前端四个服务
- `.github/workflows/ci.yml`：用 GitHub Actions 跑 pytest

## 本地运行

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

这个仓库不需要真的能跑起来——它存在的意义，是让你第一次打开 RepoLens 时，
可以点一下"示例仓库"，立刻看到一份包含前后端、数据库、容器化的技术栈报告。
