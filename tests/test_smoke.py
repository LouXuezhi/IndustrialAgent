from fastapi.testclient import TestClient

from app.main import app


def test_healthz() -> None:
    client = TestClient(app)
    resp = client.get("/api/v1/admin/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

