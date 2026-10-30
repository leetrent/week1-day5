import io
from urllib import error

import pytest

from app.ai import (
    BoardAssistantResult,
    OpenRouterConfigError,
    OpenRouterRequestError,
    OpenRouterTimeoutError,
    load_openrouter_config,
    request_board_assistant_response,
    request_chat_completion,
)
from app.board import Board, DEFAULT_BOARD


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_load_openrouter_config_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(OpenRouterConfigError, match="OPENROUTER_API_KEY is not set."):
        load_openrouter_config()


def test_request_chat_completion_maps_invalid_key_to_clear_error(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "invalid-key")

    def fake_urlopen(*_, **__):
        raise error.HTTPError(
            url="https://openrouter.ai/api/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"error":{"message":"Invalid API key"}}'),
        )

    monkeypatch.setattr("app.ai.request.urlopen", fake_urlopen)

    with pytest.raises(OpenRouterConfigError, match="OpenRouter authentication failed."):
        request_chat_completion("2+2")


def test_request_chat_completion_maps_timeout_to_clear_error(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def timeout(*_, **__):
        raise TimeoutError("timed out")

    monkeypatch.setattr("app.ai.request.urlopen", timeout)

    with pytest.raises(OpenRouterTimeoutError, match="OpenRouter request timed out."):
        request_chat_completion("2+2")


def test_request_chat_completion_maps_transient_network_failure(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def failure(*_, **__):
        raise error.URLError("temporary failure")

    monkeypatch.setattr("app.ai.request.urlopen", failure)

    with pytest.raises(OpenRouterRequestError, match="temporary failure"):
        request_chat_completion("2+2")


def test_request_chat_completion_returns_assistant_content(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_urlopen(*_, **__):
        return _FakeResponse(b'{"choices":[{"message":{"content":"4"}}]}')

    monkeypatch.setattr("app.ai.request.urlopen", fake_urlopen)

    model, content = request_chat_completion("2+2")

    assert model == "openai/gpt-oss-120b"
    assert content == "4"


def test_request_board_assistant_response_returns_reply_without_board_update(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_urlopen(*_, **__):
        return _FakeResponse(
            b'{"choices":[{"message":{"content":"{\\"reply\\":\\"No changes needed.\\",\\"board\\":null}"}}]}'
        )

    monkeypatch.setattr("app.ai.request.urlopen", fake_urlopen)
    board = Board.model_validate(DEFAULT_BOARD)

    result = request_board_assistant_response(
        board=board,
        user_message="What should I do next?",
        conversation_history=[{"role": "user", "content": "Check current priorities."}],
    )

    assert isinstance(result, BoardAssistantResult)
    assert result.reply == "No changes needed."
    assert result.board is None


def test_request_board_assistant_response_validates_and_returns_board_update(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    updated_board = Board.model_validate(DEFAULT_BOARD).model_dump(mode="json")
    updated_board["columns"][0]["title"] = "AI Updated Backlog"
    payload = {"reply": "Updated first column title.", "board": updated_board}

    def fake_urlopen(*_, **__):
        return _FakeResponse(
            json_bytes(payload)
        )

    monkeypatch.setattr("app.ai.request.urlopen", fake_urlopen)
    board = Board.model_validate(DEFAULT_BOARD)

    result = request_board_assistant_response(
        board=board,
        user_message="Rename the first column.",
        conversation_history=[],
    )

    assert result.board is not None
    assert result.board.columns[0].title == "AI Updated Backlog"


def test_request_board_assistant_response_rejects_non_json(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_urlopen(*_, **__):
        return _FakeResponse(b'{"choices":[{"message":{"content":"Not JSON"}}]}')

    monkeypatch.setattr("app.ai.request.urlopen", fake_urlopen)
    board = Board.model_validate(DEFAULT_BOARD)

    with pytest.raises(OpenRouterRequestError, match="valid JSON object"):
        request_board_assistant_response(
            board=board,
            user_message="Summarize board.",
            conversation_history=[],
        )


def test_request_board_assistant_response_rejects_invalid_board_integrity(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    broken_board = Board.model_validate(DEFAULT_BOARD).model_dump(mode="json")
    broken_board["columns"][0]["cardIds"] = ["card-does-not-exist"]
    payload = {"reply": "Applied update.", "board": broken_board}

    def fake_urlopen(*_, **__):
        return _FakeResponse(json_bytes(payload))

    monkeypatch.setattr("app.ai.request.urlopen", fake_urlopen)
    board = Board.model_validate(DEFAULT_BOARD)

    with pytest.raises(OpenRouterRequestError, match="missing card"):
        request_board_assistant_response(
            board=board,
            user_message="Apply update.",
            conversation_history=[],
        )


def test_request_board_assistant_response_prompt_defines_card_fields(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    sent_bodies: list[bytes] = []

    def fake_urlopen(req, **__):
        sent_bodies.append(req.data)
        return _FakeResponse(json_bytes({"reply": "Ok.", "board": None}))

    monkeypatch.setattr("app.ai.request.urlopen", fake_urlopen)
    empty_board = Board.model_validate(DEFAULT_BOARD).model_copy(deep=True)
    empty_board.cards = {}
    for column in empty_board.columns:
        column.cardIds = []

    request_board_assistant_response(
        board=empty_board,
        user_message="Add a card titled Test card to Backlog.",
        conversation_history=[],
    )

    import json

    system_prompt = json.loads(sent_bodies[0])["messages"][0]["content"]
    assert '"cards":{"<cardId>":{"id":"string","title":"string","details":"string"}}' in system_prompt
    assert "Every card must have id, title, and details" in system_prompt


def json_bytes(payload: dict[str, object]) -> bytes:
    import json

    return json.dumps({"choices": [{"message": {"content": json.dumps(payload)}}]}).encode("utf-8")
