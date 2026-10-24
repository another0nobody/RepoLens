"""示例项目入口：一个很小的"商城订单"服务。

这个仓库是 RepoLens 自带的演示仓库，故意用了多种技术，
方便你第一次打开网页时，不用等下载就能看到一份完整的技术栈报告。
"""

from fastapi import FastAPI

from app.api.routes import router
from app.db import init_db

app = FastAPI(title="Demo Shop API", version="1.0.0")
app.include_router(router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
