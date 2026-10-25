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
- [ ] Review current repo structure and existing frontend implementation
- [ ] Expand this file with actionable checklist tasks, tests, and success criteria for each part
- [ ] Draft `frontend/AGENTS.md` that documents:
  - current architecture and folder structure
  - state management approach
  - existing Kanban/card drag-drop behavior
  - current AI chat UI behavior (frontend-only demo status)
  - known limitations and assumptions
- [ ] Present plan and `frontend/AGENTS.md` to user for explicit sign-off
- [ ] Do not begin Part 2 until sign-off is granted

### Tests
- [ ] Manual review for completeness against all requirements in root `AGENTS.md`
- [ ] Ensure every part includes concrete implementation steps, validation steps, and pass/fail criteria

### Success criteria
- [ ] User confirms plan is approved
- [ ] `frontend/AGENTS.md` exists and accurately describes current frontend code

## Part 2: Scaffolding

### Scope
Create backend scaffold, Docker packaging, and cross-platform start/stop scripts. Serve static hello-world content and verify one API route.

### Checklist
- [ ] Create `backend/` FastAPI app with:
  - app entrypoint
  - health endpoint
  - example API endpoint for JSON response
- [ ] Create Dockerfile using Python + `uv` dependency workflow
- [ ] Add scripts in `scripts/` for Mac, Linux, and Windows:
  - start script
  - stop script
- [ ] Wire static hello-world page serving from FastAPI
- [ ] Confirm app starts in Docker and can serve both static HTML and API response

### Tests
- [ ] Container build succeeds
- [ ] Start script launches container/service without manual intervention
- [ ] `GET /` returns hello-world HTML
- [ ] Example API endpoint returns expected JSON and HTTP 200
- [ ] Stop script cleanly stops service/container

### Success criteria
- [ ] One-command local startup works on each OS script target
- [ ] Browser can load root page and API call completes successfully

## Part 3: Add in Frontend

### Scope
Build and serve existing Next.js frontend statically through backend so `/` shows the demo Kanban board.

### Checklist
- [ ] Audit frontend build output requirements
- [ ] Configure static export/build pipeline for frontend artifacts
- [ ] Integrate build output into backend static serving path
- [ ] Ensure route handling serves frontend index for root path
- [ ] Keep Docker workflow compatible with frontend build step

### Tests
- [ ] Frontend build completes without errors
- [ ] `GET /` renders Kanban UI, not hello-world placeholder
- [ ] Static assets (JS/CSS) load successfully
- [ ] Unit tests for key frontend components run and pass
- [ ] Integration test verifies page render and core board visibility

### Success criteria
- [ ] Demo Kanban board is visible at `/` in containerized run
- [ ] No regressions in existing frontend behavior

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
- [ ] Add login UI at initial entry to `/`
- [ ] Implement credential validation against hardcoded values
- [ ] Add authenticated session state (simple MVP mechanism)
- [ ] Protect board view so unauthenticated users cannot access it
- [ ] Add logout action and session clear behavior

### Tests
- [ ] Invalid credentials are rejected with clear error message
- [ ] Valid credentials show the Kanban board
- [ ] Authenticated refresh behavior matches intended MVP session design
- [ ] Logout returns user to login view
- [ ] Frontend unit/integration tests cover login, guard, and logout paths

### Success criteria
- [ ] Unauthenticated users cannot access Kanban UI
- [ ] Login and logout behavior is stable and repeatable

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
- [ ] Propose schema tables and columns for:
  - users (future multi-user support)
  - board state storage (JSON payload)
  - timestamps/versioning metadata
- [ ] Define JSON structure for board columns/cards compatible with frontend model
- [ ] Document migration/creation approach when DB file is absent
- [ ] Write design doc in `docs/` with trade-offs and rationale
- [ ] Request explicit user sign-off before implementing Part 6

### Tests
- [ ] Validate schema can represent required board operations (rename column, edit card, move card)
- [ ] Validate one board per user constraint in MVP logic
- [ ] Peer-style review checklist against root `AGENTS.md` requirements

### Success criteria
- [ ] User approves schema and documentation
- [ ] JSON structure and schema are implementation-ready

## Part 6: Backend

### Scope
Implement backend API for reading/updating Kanban per user with auto-creation of SQLite DB when missing.

### Checklist
- [ ] Add DB initialization on startup (create file/tables if missing)
- [ ] Implement API endpoints for board read/update operations
- [ ] Add request/response validation models
- [ ] Add service layer logic for per-user board retrieval and persistence
- [ ] Handle expected errors with clear HTTP responses

### Tests
- [ ] Backend unit tests for DB initialization and CRUD logic
- [ ] Endpoint tests for success and invalid input scenarios
- [ ] Verify board data persists across server restarts
- [ ] Verify isolated user board access behavior

### Success criteria
- [ ] API supports complete board lifecycle operations required by frontend
- [ ] Database reliably initializes and persists data

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
- [ ] Replace local-only board state source with API-backed fetch/update flow
- [ ] Wire board interactions (move/edit/rename) to backend persistence
- [ ] Add loading and error UI states for network operations
- [ ] Keep UI interactions responsive and consistent after API writes

### Tests
- [ ] Integration tests for initial board load from API
- [ ] Integration tests for card edits/moves and column rename persistence
- [ ] Verify state remains after refresh and restart
- [ ] Negative-path tests for API failures and retry/feedback behavior

### Success criteria
- [ ] Board state is persisted and restored correctly
- [ ] Core Kanban interactions remain stable under API-backed flow

## Part 8: AI connectivity

### Scope
Enable backend AI call through OpenRouter using `OPENROUTER_API_KEY` and model `openai/gpt-oss-120b`.

### Checklist
- [ ] Add backend client for OpenRouter API calls
- [ ] Add configuration loader for env variables
- [ ] Implement minimal test endpoint/service for connectivity
- [ ] Ensure secrets are never logged

### Tests
- [ ] Connectivity test prompt `2+2` returns successful AI response
- [ ] Missing/invalid API key path returns clear server error
- [ ] Timeouts and transient failures are surfaced cleanly

### Success criteria
- [ ] Backend can reliably call OpenRouter with configured model
- [ ] Operational errors are explicit and diagnosable

## Part 9: Structured AI board operations

### Scope
Send board JSON + user message + conversation history to AI and consume structured response containing chat reply plus optional board update payload.

### Checklist
- [ ] Define strict structured output schema
- [ ] Build prompt payload from:
  - current board JSON
  - user prompt
  - conversation history
- [ ] Parse and validate structured AI response
- [ ] Apply optional board update atomically when valid
- [ ] Persist board changes and return updated state to caller

### Tests
- [ ] Unit tests for schema validation and parse failures
- [ ] Tests for response-only path (no board update)
- [ ] Tests for valid board update path
- [ ] Tests for invalid AI output (graceful error, no corrupt state)

### Success criteria
- [ ] AI responses are consistently parsed into typed structure
- [ ] Optional board mutations are safe, validated, and persisted

## Part 10: Sidebar AI chat UI

### Scope
Add full sidebar chat experience in frontend, display AI responses, and refresh Kanban when AI returns updates.

### Checklist
- [ ] Implement sidebar chat UI with message history display
- [ ] Connect send-message action to backend AI endpoint
- [ ] Render assistant response text in chat thread
- [ ] Detect and apply returned board updates to UI state
- [ ] Auto-refresh board view after AI-driven updates
- [ ] Ensure interactions work alongside drag/drop and manual edits

### Tests
- [ ] UI tests for chat open/send/receive flow
- [ ] Integration tests for AI response that updates board
- [ ] Integration tests for AI response without board update
- [ ] Regression tests for core Kanban interactions while chat is active

### Success criteria
- [ ] Sidebar chat works end-to-end with backend AI
- [ ] Kanban updates from AI are reflected immediately and persist

## Cross-part quality gates

- [ ] Keep implementation aligned with root `AGENTS.md` as source of truth
- [ ] Keep scope limited to MVP requirements
- [ ] Add/update tests with each part before marking done
- [ ] Validate behavior in local Docker run after each major part
- [ ] Keep docs in `docs/` current as architecture evolves