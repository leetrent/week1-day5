import pytest
from httpx import ASGITransport, AsyncClient

from app.ai import BoardAssistantResult
from app.ai import OpenRouterConfigError, OpenRouterRequestError, OpenRouterTimeoutError
from app.board import Board
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


@pytest.mark.anyio
async def test_ai_smoke_endpoint_returns_response(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def fake_chat_completion(_: str) -> tuple[str, str]:
        return "openai/gpt-oss-120b", "4"

    monkeypatch.setattr("app.main.request_chat_completion", fake_chat_completion)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/ai/smoke")

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "openai/gpt-oss-120b"
    assert payload["prompt"] == "2+2"
    assert payload["response"] == "4"


@pytest.mark.anyio
async def test_ai_smoke_endpoint_missing_key_returns_clear_error(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def missing_key(_: str) -> tuple[str, str]:
        raise OpenRouterConfigError("OPENROUTER_API_KEY is not set.")

    monkeypatch.setattr("app.main.request_chat_completion", missing_key)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/ai/smoke")

    assert response.status_code == 500
    assert response.json()["detail"] == "OPENROUTER_API_KEY is not set."


@pytest.mark.anyio
async def test_ai_smoke_endpoint_invalid_key_returns_clear_error(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def invalid_key(_: str) -> tuple[str, str]:
        raise OpenRouterConfigError("OpenRouter authentication failed. Check OPENROUTER_API_KEY.")

    monkeypatch.setattr("app.main.request_chat_completion", invalid_key)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/ai/smoke")

    assert response.status_code == 500
    assert "OpenRouter authentication failed." in response.json()["detail"]


@pytest.mark.anyio
async def test_ai_smoke_endpoint_timeout_returns_gateway_timeout(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def timeout_case(_: str) -> tuple[str, str]:
        raise OpenRouterTimeoutError("OpenRouter request timed out.")

    monkeypatch.setattr("app.main.request_chat_completion", timeout_case)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/ai/smoke")

    assert response.status_code == 504
    assert response.json()["detail"] == "OpenRouter request timed out."


@pytest.mark.anyio
async def test_ai_smoke_endpoint_transient_failure_returns_bad_gateway(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def transient_failure(_: str) -> tuple[str, str]:
        raise OpenRouterRequestError("OpenRouter connection failed: temporary failure")

    monkeypatch.setattr("app.main.request_chat_completion", transient_failure)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/ai/smoke")

    assert response.status_code == 502
    assert "temporary failure" in response.json()["detail"]


@pytest.mark.anyio
async def test_ai_board_endpoint_returns_reply_without_board_update(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def no_update(board: Board, user_message: str, conversation_history: list[dict[str, str]]) -> BoardAssistantResult:
        assert isinstance(board, Board)
        assert user_message
        assert isinstance(conversation_history, list)
        return BoardAssistantResult(model="openai/gpt-oss-120b", reply="No board updates needed.", board=None)

    monkeypatch.setattr("app.main.request_board_assistant_response", no_update)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        before = await client.get("/api/board/user")
        response = await client.post(
            "/api/ai/board/user",
            json={
                "message": "Summarize what I should do next.",
                "conversation": [{"role": "user", "content": "Any quick suggestions?"}],
            },
        )
        after = await client.get("/api/board/user")

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"] == "No board updates needed."
    assert payload["board_updated"] is False
    assert payload["version"] == before.json()["version"]
    assert after.json()["version"] == before.json()["version"]


@pytest.mark.anyio
async def test_ai_board_endpoint_persists_valid_board_update(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def apply_update(board: Board, user_message: str, conversation_history: list[dict[str, str]]) -> BoardAssistantResult:
        assert user_message
        assert isinstance(conversation_history, list)
        updated_board = board.model_copy(deep=True)
        updated_board.columns[0].title = "AI Updated Backlog"
        return BoardAssistantResult(model="openai/gpt-oss-120b", reply="I renamed the first column.", board=updated_board)

    monkeypatch.setattr("app.main.request_board_assistant_response", apply_update)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        before = await client.get("/api/board/user")
        response = await client.post(
            "/api/ai/board/user",
            json={"message": "Rename the first column to AI Updated Backlog", "conversation": []},
        )
        after = await client.get("/api/board/user")

    assert response.status_code == 200
    payload = response.json()
    assert payload["board_updated"] is True
    assert payload["board"]["columns"][0]["title"] == "AI Updated Backlog"
    assert payload["version"] == before.json()["version"] + 1
    assert after.json()["board"]["columns"][0]["title"] == "AI Updated Backlog"


@pytest.mark.anyio
async def test_ai_board_endpoint_maps_auth_errors(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def auth_failure(board: Board, user_message: str, conversation_history: list[dict[str, str]]) -> BoardAssistantResult:
        assert isinstance(board, Board)
        assert user_message
        assert isinstance(conversation_history, list)
        raise OpenRouterConfigError("OpenRouter authentication failed. Check OPENROUTER_API_KEY.")

    monkeypatch.setattr("app.main.request_board_assistant_response", auth_failure)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/ai/board/user", json={"message": "Anything to update?", "conversation": []})

    assert response.status_code == 500
    assert "OpenRouter authentication failed." in response.json()["detail"]


@pytest.mark.anyio
async def test_ai_board_endpoint_maps_timeout(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def timeout_failure(board: Board, user_message: str, conversation_history: list[dict[str, str]]) -> BoardAssistantResult:
        assert isinstance(board, Board)
        assert user_message
        assert isinstance(conversation_history, list)
        raise OpenRouterTimeoutError("OpenRouter request timed out.")

    monkeypatch.setattr("app.main.request_board_assistant_response", timeout_failure)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/ai/board/user", json={"message": "Anything to update?", "conversation": []})

    assert response.status_code == 504
    assert response.json()["detail"] == "OpenRouter request timed out."


@pytest.mark.anyio
async def test_ai_board_endpoint_maps_bad_provider_response(monkeypatch, tmp_path):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    initialize_database()

    def bad_provider(board: Board, user_message: str, conversation_history: list[dict[str, str]]) -> BoardAssistantResult:
        assert isinstance(board, Board)
        assert user_message
        assert isinstance(conversation_history, list)
        raise OpenRouterRequestError("OpenRouter structured response was not a valid JSON object.")

    monkeypatch.setattr("app.main.request_board_assistant_response", bad_provider)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/ai/board/user", json={"message": "Anything to update?", "conversation": []})

    assert response.status_code == 502
    assert "valid JSON object" in response.json()["detail"]
