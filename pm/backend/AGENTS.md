# Backend notes

This folder contains the FastAPI backend scaffold for the Project Management MVP.

## Current contents

- `app/main.py`: FastAPI app entrypoint with:
  - `GET /` serving static frontend build
  - `GET /health` healthcheck endpoint
  - `GET /api/hello` example JSON API endpoint
  - `GET /api/ai/smoke` OpenRouter connectivity check (`2+2`)
  - `POST /api/ai/board/{username}` structured AI chat reply + optional board update
  - `GET /api/board/{username}` to fetch board state
  - `PUT /api/board/{username}` to persist board state
- `app/ai.py`: OpenRouter config loading, chat completion client, and structured board-operation parsing/validation
- `app/board.py`: Pydantic board schema and default board seed
- `app/db.py`: SQLite initialization and board persistence helpers
- `tests/test_ai.py`: OpenRouter configuration and error-handling tests
- `tests/test_db.py`: DB initialization and persistence tests
- `tests/test_api.py`: API endpoint tests for board CRUD and validation
- `pyproject.toml`: backend Python dependencies for `uv`-managed install

## Current purpose

This backend now supports:

- static frontend serving
- DB auto-initialization if missing
- per-user board read/write API with one-board-per-user behavior
- OpenRouter smoke-test API connectivity for Part 8
- structured AI board operations for Part 9 with optional validated board persistence