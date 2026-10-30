# Code Review: Project Management MVP (`claude-code` branch)

Date: 2026-10-30
Scope: the whole `pm/` codebase (backend, frontend, Docker, scripts, tests) at commit `060cc61`.

## Summary

The codebase is small, readable, and consistent with the "keep it simple" standard in `AGENTS.md`. The single-container, single-origin design is sound. The backend validates AI output carefully, and both stacks have reasonable test coverage.

The most important problems are about data, not code style:

1. Saved boards do not survive a container restart, because the Docker setup has no volume and the image bakes in a committed `pm.db`.
2. The frontend can overwrite the saved board with demo data, or lose edits, because of how loading and saving are sequenced.
3. One business requirement, editing cards, is not implemented.

| Severity | Count |
|----------|-------|
| High     | 3     |
| Medium   | 7     |
| Low      | 9     |

---

## High

### H1. Board data is lost on every restart in Docker

- `scripts/start-*.{sh,ps1}` run `docker rm -f` and then `docker run` with no volume (`scripts/start-windows.ps1:22`, `:28`).
- The DB lives inside the container at `/app/backend/data/pm.db` (`backend/app/db.py:16`), so each start begins with a fresh filesystem.
- `backend/data/pm.db` is tracked in git, and `.dockerignore` does not exclude it. `COPY backend ./` (`Dockerfile:23`) therefore bakes whatever was committed into the image. Each restart resets every board to that snapshot.

The requirement "SQLite local database, creating a new db if it doesn't exist" implies the data should persist between runs.

**Recommendation**

- Mount a named volume: `docker run ... -v pm-data:/app/backend/data ...` in all three start scripts.
- Remove the DB from git (`git rm --cached backend/data/pm.db`), then add `backend/data/` to `.gitignore` and `.dockerignore`.

### H2. A failed initial load can overwrite the saved board with demo data

`KanbanBoard.tsx:29` starts with `initialData`. If `fetchBoard` fails (`:62-63`), the board keeps showing demo data. The next drag, rename, or add then calls `saveBoard` with a board derived from `initialData` (`:96-101`), which permanently replaces the user's real board on the server.

The same thing can happen without any error. If the user interacts before the first `GET` returns, the change is built on top of `initialData`.

**Recommendation:** Don't render the editable board until the load finishes (show a loading state). If the load fails, show the error with a Retry button instead of falling back to demo data. Remove `initialData` from the component's initial state; it then only serves as a test fixture.

### H3. Card editing is not implemented

`AGENTS.md` requires that cards "can be moved with drag and drop, and edited". The UI supports add, remove, and move only. `KanbanCard.tsx` renders the title and details as static text. Only the AI chat can edit cards today.

**Recommendation:** Add inline editing of the title and details, for example click-to-edit using the same pattern as the column title input, and persist with `applyBoardUpdate`. Add a unit test and an e2e test.

---

## Medium

### M1. Overlapping saves can lose edits or revert the UI

Every change triggers its own `PUT` (`KanbanBoard.tsx:101`), and each response calls `setBoard(payload.board)` (`:88`). The column title saves on every keystroke (`KanbanColumn.tsx:44`), so typing "Done" sends four requests. Consequences:

- A response for an older state can arrive after a newer local edit and overwrite it on screen. With any network latency, this shows up as typed characters disappearing from the column title.
- Requests can be processed out of order on the server (FastAPI runs sync handlers in a thread pool), so the last write may not be the latest state.
- `isSyncing` turns false when the first request finishes, even while others are still pending.

**Recommendation (simple)**

- Don't apply the server's echo of a `PUT`. The client already has the state it sent.
- Save the column title on blur or Enter instead of on every keystroke.
- Serialize saves: keep one in flight, and when it finishes, send the latest `boardRef.current` if it changed.

### M2. AI responses overwrite edits made while the AI is thinking

`handleSendMessage` sends the request, and the backend reads the board *at that moment* (`main.py:114`). If the user drags a card during the wait, the AI's full board (`KanbanBoard.tsx:191-193`) replaces it. The backend also persists the AI board over any `PUT` that landed in between.

**Recommendation:** Disable drag and edit while `isAiLoading`, or use the `version` field for optimistic concurrency (see M3).

### M3. `version` is stored but never used

The DB increments `version` on each write, and the API returns it, but nothing ever checks it. It is the natural fix for M1 and M2.

**Recommendation:** Either accept `version` on `PUT` and reject stale writes with `409 Conflict` (`UPDATE ... WHERE user_id = ? AND version = ?`), or drop the column to avoid dead complexity. Given the MVP scope, the M1/M2 frontend fixes may be enough, and dropping it is acceptable.

### M4. The PUT endpoint does not validate board integrity

`_validate_board_integrity` (`ai.py:197`) runs only on AI output. `PUT /api/board/{username}` accepts any board that matches the schema, including card ids missing from `cards`. A board like that crashes the frontend: `KanbanBoard.tsx:273` maps `cardIds` to `board.cards[cardId]`, which yields `undefined`, and `KanbanCard` then reads `card.id`.

Neither check enforces the "fixed columns" requirement either. The AI can add, remove, or reorder columns (an empty column passes), and the layout hardcodes `lg:grid-cols-5` (`KanbanBoard.tsx:268`).

**Recommendation:** Move the integrity check into `board.py` as a Pydantic `model_validator` on `Board`, so every write path gets it for free. Also check that column ids match the five fixed ids. Rename the error type, since it would no longer be AI-specific.

### M5. The AI system prompt omits the rules the backend enforces

The prompt (`ai.py:240-244`) asks for JSON but never says that each card must appear exactly once, that card keys must equal ids, or that column ids must stay fixed. It also doesn't explain how to create a new card id. Every violation becomes a 502 for the user.

**Recommendation:** State the invariants in the system prompt and give an example of the board shape. Also pass `response_format: {"type": "json_object"}` in the OpenRouter payload, if the model supports it, to reduce fenced or invalid JSON.

### M6. Database connections are never closed

`with get_connection() as connection:` (`db.py:29`, `:89`, `:113`) uses `sqlite3.Connection` as a context manager. That commits or rolls back the transaction but does **not** close the connection. Connections are released only when garbage-collected.

**Recommendation:** Wrap with `contextlib.closing(get_connection())`, or close explicitly in a small helper context manager.

### M7. The API (and OpenRouter credits) are exposed on the network

The backend has no auth by design (MVP). However, the start scripts publish `-p 8000:8000`, which binds all interfaces. Anyone on the same network can read or overwrite any board and call `/api/ai/board/*`, spending the OpenRouter key's credits. `GET /api/board/{anything}` also creates a user row and a board for any name (`db.py:90`).

**Recommendation:** Bind to localhost only, `-p 127.0.0.1:8000:8000`, which costs nothing and fits "runs locally". Document that backend auth is a known MVP gap.

---

## Low

### L1. Leftover scaffolding endpoints

`/api/hello` (`main.py:82`) and `/api/ai/smoke` (`main.py:87`) were useful during the build but no longer serve the app. `/api/ai/smoke` makes a paid call that anyone can trigger. Removing them, along with `request_chat_completion` and their tests, simplifies the code.

### L2. Duplicated error mapping

The `try/except` mapping OpenRouter errors to 500, 504, and 502 is repeated in two handlers (`main.py:93-98`, `:125-130`). If L1 is done, only one copy remains. Otherwise, use FastAPI exception handlers (`@app.exception_handler(OpenRouterTimeoutError)`) once.

### L3. Unnecessary defensive code

- `model or DEFAULT_OPENROUTER_MODEL` (`main.py:101`, `:136`): `model` is always set by `load_openrouter_config`.
- `if board_updated and assistant_result.board is not None` (`main.py:123`): this is the same condition checked twice.
- `if row is None: raise RuntimeError(...)` after an insert or update (`db.py:100`, `:128`) can't happen.
- `ai.py:249-256` re-validates conversation roles and content that `AiConversationMessage` already validated.
- `useMemo(() => board.cards, [board.cards])` (`KanbanBoard.tsx:78`) memoizes a property access.

`AGENTS.md` says "NO unnecessary defensive programming", so these can go.

### L4. Board shape and default board defined twice

`DEFAULT_BOARD` (`board.py:32`) and `initialData` (`kanban.ts:18`) must be kept in sync by hand. Once H2 is fixed, the frontend no longer needs `initialData` at runtime, so it can move to test fixtures. The backend then becomes the single source of truth for the default board.

### L5. Unbounded AI request size

The full conversation history plus the full board is sent on every message (`ai.py:249-269`), with no limit. Long sessions grow cost and latency and can eventually exceed the model context. Cap history, for example to the last 20 messages, on the client or the server.

### L6. Repository hygiene

- `frontend/test-results/.last-run.json` is tracked. Add `frontend/test-results/` and `frontend/playwright-report/` to `.gitignore`.
- `.env` is excluded from git but not from `.dockerignore`. It isn't copied into the image today, but it is sent to the Docker build context. Add it.
- The root `.gitignore` is the large generic Python template, and most of its entries don't apply. Optional cleanup.

### L7. Non-reproducible Python install in Docker

`Dockerfile:20-21` copies `pyproject.toml` but not `uv.lock`, so `uv sync` resolves fresh versions on every build. Copy `uv.lock` and use `uv sync --frozen --no-dev --no-install-project`. Optionally, use the official `ghcr.io/astral-sh/uv` image instead of `pip install uv`.

### L8. Start scripts depend on the current directory

`start-windows.ps1:6` uses `Get-Location`, and the shell scripts use a relative `.env` and build context `.`. Running a script from inside `scripts/` fails. Resolve paths from the script's own location (`$PSScriptRoot\..` and `"$(dirname "$0")/.."`).

### L9. Minor UX gaps

- A column title can be cleared to an empty string, with no validation on either side.
- Deleting a card has no confirmation or undo.
- If an AI request fails, the user's message stays in the chat history with no reply. The next request then sends two consecutive `user` messages. Remove the failed message, or mark it as failed and exclude it from history.
- The chat `textarea` doesn't submit on Enter.

---

## Testing

**Strengths**

- Backend tests use an isolated temp DB through `PM_DB_PATH` and mock the network.
- Error mapping (500, 504, 502) is covered at both the unit and API levels.
- Frontend unit tests cover load and save failures, plus AI failure paths.

**Gaps**

- **No test runs against the real backend.** All Playwright tests mock `/api/*` (`tests/kanban.spec.ts:6`). A mismatch between the frontend and the backend contract (for example, a field rename in `board.py`) would pass every test. Add one e2e test against the Docker app, or run Playwright against `uvicorn` serving the built `out/`.
- There is no test for H1 (persistence across a container restart). This can be a manual smoke step in `scripts/AGENTS.md`.
- Nothing tests `_resolve_static_path` against path traversal (for example, `GET /..%2f..%2fetc/passwd`). The code looks correct, so a single test would lock it in.
- `moveCard` has three tests. Add cases for dropping onto an empty column and for unknown ids.
- `test_api.py` repeats the same 4-line setup in every test. A `client` fixture in `conftest.py` would cut about 60 lines.

---

## What is done well

- **Clear architecture.** One container and one origin, so no CORS and no proxy, and every API route lives under `/api/`.
- **Careful AI output handling.** It tolerates fenced JSON, validates the schema, checks integrity, and maps errors to the right status codes.
- **Simple data model.** One JSON document per user, with a `json_valid` check constraint.
- **Path-traversal-safe static serving.** It uses `resolve()` and checks parents.
- **Typed frontend.** Small components and an API layer with explicit response checks.
- **Follows the brief.** The color scheme comes from `AGENTS.md` through CSS variables, and there are no emojis.

---

## Recommended order of work

1. **H1:** add the volume, untrack `pm.db`, and update the ignore files. This is small and high value.
2. **H2:** add a loading and error state, and stop falling back to demo data.
3. **M1:** save the column title on blur and serialize saves.
4. **M4 + M5:** move the integrity check into `Board`, enforce fixed columns, and tighten the AI prompt.
5. **H3:** add card editing.
6. **M6, M7:** close connections and bind to localhost.
7. The Low items and test gaps, as time permits.
