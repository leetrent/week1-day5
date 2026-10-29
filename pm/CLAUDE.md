# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Read `AGENTS.md` (root) first: it holds the business requirements, technical decisions, color scheme, and coding standards (keep it simple, no over-engineering, no emojis, prove root cause before fixing). Per-folder notes live in `backend/AGENTS.md`, `frontend/AGENTS.md`, and `scripts/AGENTS.md`. Planning docs are in `docs/` (`PLAN.md` tracks the 10-part build plan; `DATABASE_SCHEMA.md` holds the approved schema).

## Commands

Full app (Docker, serves on http://localhost:8000; requires `.env` in the project root with `OPENROUTER_API_KEY`):

```
scripts/start-windows.ps1   # or start-mac.sh / start-linux.sh
scripts/stop-windows.ps1    # or stop-mac.sh / stop-linux.sh
```

Backend (run from `backend/`):

```
uv sync
uv run pytest
uv run pytest tests/test_api.py::test_health_endpoint
uv run uvicorn app.main:app --reload
```

Frontend (run from `frontend/`):

```
npm install
npm run dev                     # http://localhost:3000, no backend proxy
npm run lint
npm run build                   # static export to frontend/out
npm run test:unit
npx vitest run src/lib/kanban.test.ts
npm run test:e2e                # Playwright; starts dev server on 127.0.0.1:3000
npx playwright test -g "moves a card"
```

## Architecture

- **Single container, single origin.** The Dockerfile builds the Next.js app with `output: "export"` and copies `frontend/out` into `backend/static`. FastAPI serves `/` and a catch-all `/{full_path}` from that directory (falling back to `index.html`), and every API route lives under `/api/`. The frontend calls relative `/api/...` URLs, so there is no CORS config and no dev proxy. `backend/static/index.html` in git is only a placeholder that the Docker build overwrites.
- **Auth is frontend-only.** `AuthGate.tsx` checks the hardcoded `user`/`password` and stores the session in `sessionStorage`. The backend has no auth and identifies the user by the `{username}` path segment. Any unknown username gets a user row and a default board created on first access (`_ensure_user_and_board` in `app/db.py`).
- **Board is one JSON document per user.** SQLite tables `users` and `boards` (`UNIQUE user_id`, `board_json` with a `json_valid` check, `version` incremented on each write). Every write replaces the whole board. The DB path defaults to `backend/data/pm.db` and can be overridden with `PM_DB_PATH`, which tests use with `tmp_path`. The schema is created on app startup through the FastAPI lifespan.
- **The board shape is defined twice and must stay in sync:** the Pydantic models plus `DEFAULT_BOARD` in `backend/app/board.py`, and the TS types plus `initialData` in `frontend/src/lib/kanban.ts`. Shape: `{columns: [{id, title, cardIds}], cards: {id: {id, title, details}}}`.
- **AI flow (`POST /api/ai/board/{username}`).** `app/ai.py` calls the OpenRouter chat completions endpoint directly with `urllib` (no SDK). It sends a system prompt asking for JSON `{"reply", "board": null | full board}`, the conversation history, and the current board JSON. The response is parsed (fenced JSON is tolerated), validated against `Board`, and checked for integrity: every card is placed exactly once and keys match ids. If a board is returned, it is persisted. The frontend applies the returned `board` directly. OpenRouter errors map to HTTP 500 (config/auth), 504 (timeout), and 502 (other). Env vars: `OPENROUTER_API_KEY`, plus optional `OPENROUTER_MODEL` (default `openai/gpt-oss-120b`) and `OPENROUTER_TIMEOUT_SECONDS`.
- **Frontend state.** `KanbanBoard.tsx` owns board state, drag and drop (dnd-kit), the sync status, and the AI chat sidebar. It loads with `fetchBoard` and calls `saveBoard` (`src/lib/api.ts`) after each change.

## Notes

- The backend does not load `.env` itself. Locally, export the variables before running uvicorn; in Docker they come from `--env-file`.
- Backend tests use `httpx.AsyncClient` with `ASGITransport` and `@pytest.mark.anyio`, and monkeypatch the AI functions, so no network calls are made.
- `frontend/AGENTS.md` warns that Next.js 16 differs from older versions. Check `frontend/node_modules/next/dist/docs/` before writing Next-specific code.
