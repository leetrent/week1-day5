import pytest
from httpx import ASGITransport, AsyncClient

from app.db import initialize_database
from app.main import app


@pytest.mark.anyio
async def test_health_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_get_board_endpoint_returns_default_board(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/board/user")

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "user"
    assert payload["version"] == 1
    assert len(payload["board"]["columns"]) == 5


@pytest.mark.anyio
async def test_update_board_endpoint_persists_updates(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        initial = (await client.get("/api/board/user")).json()
        board = initial["board"]
        board["columns"][0]["title"] = "Renamed via API"

        updated = await client.put("/api/board/user", json={"board": board})
        reloaded = await client.get("/api/board/user")

    assert updated.status_code == 200
    assert updated.json()["version"] == initial["version"] + 1
    assert reloaded.status_code == 200
    assert reloaded.json()["board"]["columns"][0]["title"] == "Renamed via API"


@pytest.mark.anyio
async def test_update_board_endpoint_rejects_invalid_shape(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.put("/api/board/user", json={"board": {"columns": []}})

    assert response.status_code == 422
