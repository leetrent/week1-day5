# High-level steps for project

1. **Part 1: Plan**
   - Enrich this document with detailed checklists, tests, and success criteria for each part.
   - Create `frontend/AGENTS.md` that describes the existing frontend code.
   - Ensure the user reviews and approves the plan.

2. **Part 2: Scaffolding**
   - Set up Docker infrastructure.
   - Build backend scaffold in `backend/` with FastAPI.
   - Add start/stop scripts in `scripts/` for Mac, Linux, and Windows.
   - Serve example static HTML and confirm an API call works locally.

3. **Part 3: Add in frontend**
   - Build and serve the frontend statically.
   - Display the demo Kanban board at `/`.
   - Add comprehensive unit and integration tests.

4. **Part 4: Add a fake user sign-in experience**
   - Require login at `/` with dummy credentials (`user`, `password`) before Kanban is visible.
   - Support logout.
   - Add comprehensive tests.

5. **Part 5: Database modeling**
   - Propose a JSON-based Kanban storage schema in SQLite.
   - Document the approach in `docs/`.
   - Get explicit user sign-off.

6. **Part 6: Backend**
   - Add API routes to read and change the Kanban for a given user.
   - Add thorough backend unit tests.
   - Ensure DB is created automatically if it does not exist.

7. **Part 7: Frontend + backend**
   - Integrate frontend with backend API for persistence.
   - Test thoroughly.

8. **Part 8: AI connectivity**
   - Add OpenRouter connectivity from backend.
   - Verify with a simple `2+2` prompt test.

9. **Part 9: Structured AI board operations**
   - Send board JSON, user question, and conversation history to the AI.
   - Consume structured outputs with chat response and optional Kanban updates.
   - Test thoroughly.

10. **Part 10: Sidebar AI chat UI**
    - Build a sidebar chat widget in the UI.
    - Allow AI responses to optionally update Kanban state.
    - Refresh UI automatically after AI-driven updates.

---

# Detailed execution plan and checklists

## Part 1: Plan

### Scope
Create a detailed implementation plan for Parts 2-10, define test strategy per part, and create `frontend/AGENTS.md` describing the existing frontend codebase.

### Checklist
- [x] Review current repo structure and existing frontend implementation
- [x] Expand this file with actionable checklist tasks, tests, and success criteria for each part
- [x] Draft `frontend/AGENTS.md` that documents:
  - current architecture and folder structure
  - state management approach
  - existing Kanban/card drag-drop behavior
  - current AI chat UI behavior (frontend-only demo status)
  - known limitations and assumptions
- [x] Present plan and `frontend/AGENTS.md` to user for explicit sign-off
- [x] Do not begin Part 2 until sign-off is granted

### Tests
- [x] Manual review for completeness against all requirements in root `AGENTS.md`
- [x] Ensure every part includes concrete implementation steps, validation steps, and pass/fail criteria

### Success criteria
- [x] User confirms plan is approved
- [x] `frontend/AGENTS.md` exists and accurately describes current frontend code

## Part 2: Scaffolding

### Scope
Create backend scaffold, Docker packaging, and cross-platform start/stop scripts. Serve static hello-world content and verify one API route.

### Checklist
- [x] Create `backend/` FastAPI app with:
  - app entrypoint
  - health endpoint
  - example API endpoint for JSON response
- [x] Create Dockerfile using Python + `uv` dependency workflow
- [x] Add scripts in `scripts/` for Mac, Linux, and Windows:
  - start script
  - stop script
- [x] Wire static hello-world page serving from FastAPI
- [x] Confirm app starts in Docker and can serve both static HTML and API response

### Tests
- [x] Container build succeeds
- [x] Start script launches container/service without manual intervention
- [x] `GET /` returns hello-world HTML
- [x] Example API endpoint returns expected JSON and HTTP 200
- [x] Stop script cleanly stops service/container

### Success criteria
- [x] One-command local startup works on each OS script target
- [x] Browser can load root page and API call completes successfully

## Part 3: Add in Frontend

### Scope
Build and serve existing Next.js frontend statically through backend so `/` shows the demo Kanban board.

### Checklist
- [x] Audit frontend build output requirements
- [x] Configure static export/build pipeline for frontend artifacts
- [x] Integrate build output into backend static serving path
- [x] Ensure route handling serves frontend index for root path
- [x] Keep Docker workflow compatible with frontend build step

### Tests
- [x] Frontend build completes without errors
- [x] `GET /` renders Kanban UI, not hello-world placeholder
- [x] Static assets (JS/CSS) load successfully
- [x] Unit tests for key frontend components run and pass
- [x] Integration test verifies page render and core board visibility

### Success criteria
- [x] Demo Kanban board is visible at `/` in containerized run
- [x] No regressions in existing frontend behavior

### Part 3 manual verification (Pass/Fail)

| Check | Expected result | Status (Pass/Fail) | Notes |
|---|---|---|---|
| Start script runs | Docker image builds and container starts without errors | Pass | Verified via `scripts/start-windows.ps1` |
| Root page serves frontend | `http://localhost:8000/` shows **Kanban Studio** (not hello-world page) | Pass | `ROOT_HAS_KANBAN=True`, hello placeholder absent |
| Five columns visible | Board renders with 5 columns | Pass | Verified in automated unit + e2e tests |
| Column rename works | Editing a column title updates immediately in UI | Pass | Verified in unit test (`renames a column`) |
| Add card works | New card can be added to a column and appears in UI | Pass | Verified in unit + e2e tests |
| Drag/drop works | Card can be moved between columns successfully | Pass | Verified in e2e test (`moves a card between columns`) |
| Health endpoint works | `GET /health` returns `{"status":"ok"}` | Pass | Validated during Docker endpoint checks |
| API hello endpoint works | `GET /api/hello` returns `{"message":"Hello from FastAPI backend"}` | Pass | Validated during Docker endpoint checks |
| Static assets load | Page styling and scripts load correctly (no broken UI) | Pass | `_next/static` assets detected from root response |
| Stop script runs | Container stops and is removed cleanly | Pass | Verified via `scripts/stop-windows.ps1` |

**Part 3 final status:** Pass  
**Tester:** Copilot agent (automated checks)  
**Date:** 2026-10-24  

## Part 4: Fake user sign-in experience

### Scope
Add a simple login/logout flow using fixed credentials (`user` / `password`) and gate Kanban access.

### Checklist
- [x] Add login UI at initial entry to `/`
- [x] Implement credential validation against hardcoded values
- [x] Add authenticated session state (simple MVP mechanism)
- [x] Protect board view so unauthenticated users cannot access it
- [x] Add logout action and session clear behavior

### Tests
- [x] Invalid credentials are rejected with clear error message
- [x] Valid credentials show the Kanban board
- [x] Authenticated refresh behavior matches intended MVP session design
- [x] Logout returns user to login view
- [x] Frontend unit/integration tests cover login, guard, and logout paths

### Success criteria
- [x] Unauthenticated users cannot access Kanban UI
- [x] Login and logout behavior is stable and repeatable

### Part 4 manual verification (Pass/Fail)

| Check | Expected result | Status (Pass/Fail) | Notes |
|---|---|---|---|
| Login screen appears first | `http://localhost:8000/` shows Sign in before board access | Pass | Verified in unit + e2e tests and Docker run |
| Invalid credentials rejected | Wrong password shows clear error and does not show board | Pass | Error message: `Invalid credentials. Use user / password.` |
| Valid credentials grant access | `user` / `password` opens Kanban board | Pass | Verified in unit + e2e tests |
| Board remains gated pre-auth | Kanban interactions are unavailable until successful login | Pass | Board tests now sign in first |
| Logout works | Clicking `Log out` returns user to login screen | Pass | Verified in unit + e2e tests |
| Health endpoint unaffected | `GET /health` still returns `{"status":"ok"}` | Pass | Verified during Docker validation |
| API hello endpoint unaffected | `GET /api/hello` still returns expected JSON message | Pass | Verified during Docker validation |
| Docker start/stop still works | App starts and stops cleanly with scripts | Pass | Verified with Windows scripts |

**Part 4 final status:** Pass  
**Tester:** Copilot agent (automated checks)  
**Date:** 2026-10-24  

### Part 4 command checklist (copy/paste)

#### Git Bash (Windows) / Linux / macOS

```bash
# from repo root
bash ./scripts/start-linux.sh

# verify app + API
curl http://localhost:8000/health
curl http://localhost:8000/api/hello

# stop app
bash ./scripts/stop-linux.sh
```

#### PowerShell (Windows)

```powershell
# from repo root
powershell -ExecutionPolicy Bypass -File .\scripts\start-windows.ps1

# verify app + API
curl http://localhost:8000/health
curl http://localhost:8000/api/hello

# stop app
powershell -ExecutionPolicy Bypass -File .\scripts\stop-windows.ps1
```

#### Manual UI steps

1. Open `http://localhost:8000/`.
2. Confirm **Sign in** appears first.
3. Try invalid credentials: `user` / `wrong-password` and confirm error.
4. Sign in with `user` / `password` and confirm **Kanban Studio** appears.
5. Click **Log out** and confirm return to **Sign in**.

## Part 5: Database modeling

### Scope
Define SQLite schema for users + per-user board data persisted as JSON; document the approach and obtain approval before implementation.

Design artifact: `docs/DATABASE_SCHEMA.md`

### Checklist
- [x] Propose schema tables and columns for:
  - users (future multi-user support)
  - board state storage (JSON payload)
  - timestamps/versioning metadata
- [x] Define JSON structure for board columns/cards compatible with frontend model
- [x] Document migration/creation approach when DB file is absent
- [x] Write design doc in `docs/` with trade-offs and rationale
- [x] Request explicit user sign-off before implementing Part 6

### Tests
- [x] Validate schema can represent required board operations (rename column, edit card, move card)
- [x] Validate one board per user constraint in MVP logic
- [x] Peer-style review checklist against root `AGENTS.md` requirements

### Success criteria
- [x] User approves schema and documentation
- [x] JSON structure and schema are implementation-ready

## Part 6: Backend

### Scope
Implement backend API for reading/updating Kanban per user with auto-creation of SQLite DB when missing.

### Checklist
- [x] Add DB initialization on startup (create file/tables if missing)
- [x] Implement API endpoints for board read/update operations
- [x] Add request/response validation models
- [x] Add service layer logic for per-user board retrieval and persistence
- [x] Handle expected errors with clear HTTP responses

### Tests
- [x] Backend unit tests for DB initialization and CRUD logic
- [x] Endpoint tests for success and invalid input scenarios
- [x] Verify board data persists across server restarts
- [x] Verify isolated user board access behavior

### Success criteria
- [x] API supports complete board lifecycle operations required by frontend
- [x] Database reliably initializes and persists data

### Part 6 manual verification (Pass/Fail)

| Check | Expected result | Status (Pass/Fail) | Notes |
|---|---|---|---|
| Backend tests pass | `uv run --directory backend --group dev pytest -q` passes | Pass | 7 passed |
| DB auto-creates on startup | Missing DB file is created automatically | Pass | `backend/data/pm.db` created during startup |
| Default user board loads | `GET /api/board/user` returns 200 with board payload | Pass | Includes `columns`, `cards`, `version`, `updated_at` |
| Board update persists | `PUT /api/board/user` updates board and increments version | Pass | Verified by read -> update -> read flow |
| Invalid board shape rejected | Invalid payload returns validation error | Pass | Endpoint returns 422 |
| Existing API endpoints unaffected | `/health` and `/api/hello` still return expected responses | Pass | Verified during Docker validation |
| Docker workflow still works | Start/build/stop scripts still work end-to-end | Pass | Verified on Windows scripts |

**Part 6 final status:** Pass  
**Tester:** Copilot agent (automated checks)  
**Date:** 2026-10-24  

### Part 6 command checklist (copy/paste)

#### Run backend tests

```bash
uv run --directory backend --group dev pytest -q
```

#### Start app

Git Bash / Linux / macOS:

```bash
bash ./scripts/start-linux.sh
```

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-windows.ps1
```

#### Verify board read API

```bash
curl http://localhost:8000/api/board/user
```

#### Verify board update API (PowerShell)

```powershell
$boardResp = Invoke-RestMethod -Uri "http://localhost:8000/api/board/user"
$boardResp.board.columns[0].title = "Manual Test Rename"
$payload = @{ board = $boardResp.board } | ConvertTo-Json -Depth 20
Invoke-RestMethod -Method Put -Uri "http://localhost:8000/api/board/user" -ContentType "application/json" -Body $payload
Invoke-RestMethod -Uri "http://localhost:8000/api/board/user"
```

#### Verify validation on invalid payload

```bash
curl -X PUT http://localhost:8000/api/board/user -H "Content-Type: application/json" -d "{\"board\":{\"columns\":[]}}"
```

#### Stop app

Git Bash / Linux / macOS:

```bash
bash ./scripts/stop-linux.sh
```

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-windows.ps1
```

## Part 7: Frontend + Backend integration

### Scope
Connect frontend board operations to backend API and make Kanban persistent.

### Checklist
- [x] Replace local-only board state source with API-backed fetch/update flow
- [x] Wire board interactions (move/edit/rename) to backend persistence
- [x] Add loading and error UI states for network operations
- [x] Keep UI interactions responsive and consistent after API writes

### Tests
- [x] Integration tests for initial board load from API
- [x] Integration tests for card edits/moves and column rename persistence
- [x] Verify state remains after refresh and restart
- [x] Negative-path tests for API failures and retry/feedback behavior

### Success criteria
- [x] Board state is persisted and restored correctly
- [x] Core Kanban interactions remain stable under API-backed flow

### Part 7 verification refresh (2026-10-25)

Validation run completed to confirm Part 7 remains stable after latest integration changes.

| Check | Expected result | Status (Pass/Fail) | Notes |
|---|---|---|---|
| Backend persistence tests | `uv run --directory backend --group dev pytest -q` passes | Pass | 7 passed |
| Frontend unit integration surfaces | `npm run test:unit -- src/components/KanbanBoard.test.tsx src/components/AuthGate.test.tsx` passes | Pass | 2 files, 7 tests passed |
| Frontend e2e board integration | `npm run test:e2e -- tests/kanban.spec.ts` passes | Pass | 5 tests passed |
| Persist after refresh | Board updates survive page reload | Pass | Verified by `keeps board changes after refresh via API persistence` |
| Login + board integration | Auth gate still works with API-backed board | Pass | Verified by e2e login/logout coverage |

Design decisions update:
- No new design decisions were introduced during this verification pass.
- Existing Part 7 implementation remains: optimistic local UI updates with backend sync and user-visible sync/error status in the board header.

### Part 7 failure-path tests (2026-10-29)

| Check | Expected result | Status (Pass/Fail) | Notes |
|---|---|---|---|
| Load failure | Error message shown, local board still rendered | Pass | `KanbanBoard.test.tsx`: `shows an error and keeps the local board when loading fails` |
| Save failure and retry | Error message shown, local edit kept, error cleared after next successful save | Pass | `KanbanBoard.test.tsx`: `shows an error when saving fails and clears it after a successful retry` |
| AI request failure | Chat error shown, board unchanged | Pass | `KanbanBoard.test.tsx`: `shows a chat error when the AI request fails and leaves the board unchanged` |
| Full suite | Backend, frontend unit, e2e, lint, and build pass | Pass | 26 backend, 16 unit, 7 e2e passed; lint clean |

**Part 7 final status:** Pass  
**Tester:** Claude Code (automated checks)  
**Date:** 2026-10-29

## Part 8: AI connectivity

### Scope
Enable backend AI call through OpenRouter using `OPENROUTER_API_KEY` and model `openai/gpt-oss-120b`.

### Checklist
- [x] Add backend client for OpenRouter API calls
- [x] Add configuration loader for env variables
- [x] Implement minimal test endpoint/service for connectivity
- [x] Ensure secrets are never logged

### Tests
- [x] Connectivity test prompt `2+2` returns successful AI response
- [x] Missing/invalid API key path returns clear server error
- [x] Timeouts and transient failures are surfaced cleanly

### Success criteria
- [x] Backend can reliably call OpenRouter with configured model
- [x] Operational errors are explicit and diagnosable

### Part 8 verification (Pass/Fail)

| Check | Expected result | Status (Pass/Fail) | Notes |
|---|---|---|---|
| Backend test suite | `uv run --directory backend --group dev pytest -q` passes | Pass | 17 passed |
| AI smoke endpoint success path | `GET /api/ai/smoke` returns 200 with model, prompt, and response fields | Pass | Verified with ASGI `AsyncClient`; prompt `2+2` returned `4` |
| OpenRouter direct service check | Backend OpenRouter service returns response for prompt `2+2` | Pass | Returned `2 + 2 = 4.` |
| Missing key error path | Missing `OPENROUTER_API_KEY` returns clear configuration error | Pass | Covered by `test_load_openrouter_config_requires_api_key` and API error mapping test |
| Invalid key error path | Invalid API key maps to explicit authentication error text | Pass | Covered by `test_request_chat_completion_maps_invalid_key_to_clear_error` and API mapping test |
| Timeout and transient failure paths | Timeout returns 504 and transient connection failures return 502 | Pass | Covered by API tests (`timeout` and `transient_failure`) and service-level tests |
| Docker runtime env wiring | Start scripts pass root `.env` into container as runtime env vars | Pass | Added `--env-file .env` and missing-file guard in all start scripts |

**Part 8 final status:** Pass  
**Tester:** Copilot agent (automated checks + live OpenRouter connectivity check)  
**Date:** 2026-10-25

## Part 9: Structured AI board operations

### Scope
Send board JSON + user message + conversation history to AI and consume structured response containing chat reply plus optional board update payload.

### Checklist
- [x] Define strict structured output schema
- [x] Build prompt payload from:
  - current board JSON
  - user prompt
  - conversation history
- [x] Parse and validate structured AI response
- [x] Apply optional board update atomically when valid
- [x] Persist board changes and return updated state to caller

### Tests
- [x] Unit tests for schema validation and parse failures
- [x] Tests for response-only path (no board update)
- [x] Tests for valid board update path
- [x] Tests for invalid AI output (graceful error, no corrupt state)

### Success criteria
- [x] AI responses are consistently parsed into typed structure
- [x] Optional board mutations are safe, validated, and persisted

### Part 9 verification (Pass/Fail)

| Check | Expected result | Status (Pass/Fail) | Notes |
|---|---|---|---|
| Backend test suite | `uv run --directory backend --group dev pytest -q` passes | Pass | 26 passed |
| Structured AI endpoint available | `POST /api/ai/board/{username}` accepts message + conversation and returns structured response | Pass | Added response fields: `reply`, `board_updated`, `board`, `version`, `updated_at` |
| Prompt payload completeness | AI request includes current board JSON, user prompt, and conversation history | Pass | Implemented in `request_board_assistant_response` message construction |
| Response-only path | AI response with `board: null` does not mutate persisted board | Pass | Covered by API test `test_ai_board_endpoint_returns_reply_without_board_update` |
| Board update path | AI response with valid board payload updates DB atomically and increments version | Pass | Covered by API test `test_ai_board_endpoint_persists_valid_board_update` |
| Invalid AI output handling | Non-JSON / invalid board payloads are rejected with explicit errors and no silent fallback | Pass | Covered by service tests for parse failures and board-integrity validation |
| Timeout and provider failures | Timeout maps to 504 and provider response failures map to 502 | Pass | Covered by API tests for timeout + bad provider response |
| Live OpenRouter board-operation check | End-to-end call returns successful structured response | Pass | Verified with prompt `What is 2+2? ... do not change the board`, returned `board_updated=false` |

**Part 9 final status:** Pass  
**Tester:** Copilot agent (automated checks + live OpenRouter endpoint check)  
**Date:** 2026-10-25

## Part 10: Sidebar AI chat UI

### Scope
Add full sidebar chat experience in frontend, display AI responses, and refresh Kanban when AI returns updates.

### Checklist
- [x] Implement sidebar chat UI with message history display
- [x] Connect send-message action to backend AI endpoint
- [x] Render assistant response text in chat thread
- [x] Detect and apply returned board updates to UI state
- [x] Auto-refresh board view after AI-driven updates
- [x] Ensure interactions work alongside drag/drop and manual edits

### Tests
- [x] UI tests for chat open/send/receive flow
- [x] Integration tests for AI response that updates board
- [x] Integration tests for AI response without board update
- [x] Regression tests for core Kanban interactions while chat is active

### Success criteria
- [x] Sidebar chat works end-to-end with backend AI
- [x] Kanban updates from AI are reflected immediately and persist

### Part 10 verification (Pass/Fail)

| Check | Expected result | Status (Pass/Fail) | Notes |
|---|---|---|---|
| Frontend unit tests | `npm run test:unit -- src/components/KanbanBoard.test.tsx` passes | Pass | 5 passed |
| Frontend e2e tests | `npm run test:e2e -- tests/kanban.spec.ts` passes | Pass | 7 passed |
| Chat open/send/receive flow | Sidebar can be hidden/opened, user message sent, assistant reply rendered | Pass | Covered by unit + e2e tests |
| AI no-update integration | AI response without board update leaves board state unchanged | Pass | Covered by unit (`opens chat and shows AI response without board update`) and e2e test |
| AI update integration | AI response with board update refreshes board UI immediately and persists across refresh | Pass | Covered by unit + e2e tests |
| Drag/drop regression with chat open | Card movement still works while AI sidebar is open | Pass | Covered by e2e test `moves a card between columns while chat is open` |

**Part 10 final status:** Pass  
**Tester:** Copilot agent (automated unit + e2e checks)  
**Date:** 2026-10-26

## Cross-part quality gates

- [x] Keep implementation aligned with root `AGENTS.md` as source of truth
- [x] Keep scope limited to MVP requirements
- [x] Add/update tests with each part before marking done
- [x] Validate behavior in local Docker run after each major part
- [x] Keep docs in `docs/` current as architecture evolves