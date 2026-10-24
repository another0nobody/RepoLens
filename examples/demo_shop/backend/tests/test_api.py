"""接口测试：用 TestClient 直接调用 FastAPI，不需要真的启动服务。"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_read_missing_order(client: TestClient) -> None:
    response = client.get("/api/orders/999999")
    assert response.status_code == 404
