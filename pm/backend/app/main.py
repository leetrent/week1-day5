from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from fastapi.responses import FileResponse
from app.ai import (
    DEFAULT_OPENROUTER_MODEL,
    BoardAssistantResult,
    OpenRouterConfigError,
    OpenRouterRequestError,
    OpenRouterTimeoutError,
    request_board_assistant_response,
    request_chat_completion,
)
from app.board import Board, BoardResponse, BoardUpdateRequest
from app.db import get_board_for_user, initialize_database, update_board_for_user


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="PM MVP Backend", version="0.1.0", lifespan=lifespan)


class AiSmokeResponse(BaseModel):
    model: str
    prompt: str
    response: str


class AiConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def content_cannot_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Conversation message content cannot be empty.")
        return normalized


class AiBoardRequest(BaseModel):
    message: str
    conversation: list[AiConversationMessage] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def message_cannot_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Message cannot be empty.")
        return normalized


class AiBoardResponse(BaseModel):
    username: str
    model: str
    reply: str
    board_updated: bool
    board: Board
    version: int
    updated_at: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def api_hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI backend"}


@app.get("/api/ai/smoke", response_model=AiSmokeResponse)
def ai_smoke_test() -> dict[str, str]:
    prompt = "2+2"

    try:
        model, response_text = request_chat_completion(prompt)
    except OpenRouterConfigError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except OpenRouterTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except OpenRouterRequestError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {
        "model": model or DEFAULT_OPENROUTER_MODEL,
        "prompt": prompt,
        "response": response_text,
    }


@app.post("/api/ai/board/{username}", response_model=AiBoardResponse)
def ai_board_assistant(username: str, payload: AiBoardRequest) -> dict[str, object]:
    normalized_username = username.strip()
    if not normalized_username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")

    try:
        current_board_state = get_board_for_user(normalized_username)
        assistant_result: BoardAssistantResult = request_board_assistant_response(
            board=current_board_state["board"],
            user_message=payload.message,
            conversation_history=[message.model_dump() for message in payload.conversation],
        )

        board_updated = assistant_result.board is not None
        persisted_state = current_board_state
        if board_updated and assistant_result.board is not None:
            persisted_state = update_board_for_user(normalized_username, assistant_result.board)
    except OpenRouterConfigError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except OpenRouterTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except OpenRouterRequestError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except sqlite3.Error as error:
        raise HTTPException(status_code=500, detail=f"Database operation failed: {error}") from error

    return {
        "username": normalized_username,
        "model": assistant_result.model or DEFAULT_OPENROUTER_MODEL,
        "reply": assistant_result.reply,
        "board_updated": board_updated,
        "board": persisted_state["board"],
        "version": persisted_state["version"],
        "updated_at": persisted_state["updated_at"],
    }


@app.get("/api/board/{username}", response_model=BoardResponse)
def get_board(username: str) -> dict[str, object]:
    normalized_username = username.strip()
    if not normalized_username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")

    try:
        return get_board_for_user(normalized_username)
    except sqlite3.Error as error:
        raise HTTPException(status_code=500, detail=f"Database read failed: {error}") from error


@app.put("/api/board/{username}", response_model=BoardResponse)
def update_board(username: str, payload: BoardUpdateRequest) -> dict[str, object]:
    normalized_username = username.strip()
    if not normalized_username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")

    try:
        return update_board_for_user(normalized_username, payload.board)
    except sqlite3.Error as error:
        raise HTTPException(status_code=500, detail=f"Database write failed: {error}") from error


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(INDEX_HTML)


def _resolve_static_path(request_path: str) -> Path | None:
    static_root = STATIC_DIR.resolve()
    candidate = (STATIC_DIR / request_path).resolve()
    if static_root not in candidate.parents:
        return None
    if candidate.is_file():
        return candidate
    return None


@app.get("/{full_path:path}", include_in_schema=False)
def static_assets(full_path: str) -> FileResponse:
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")

    file_path = _resolve_static_path(full_path)
    if file_path is not None:
        return FileResponse(file_path)

    return FileResponse(INDEX_HTML)
