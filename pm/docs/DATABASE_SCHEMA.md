# Part 5: Database modeling (proposal)

## Scope

This proposal defines a SQLite schema for:

- future multi-user support
- one Kanban board per user for MVP
- board persistence as JSON compatible with the current frontend data model

This is a design document for sign-off before backend implementation in Part 6.

## Requirements mapping

- **MVP login** remains hardcoded (`user` / `password`) in frontend for now.
- **Database still supports multiple users** for future migration away from hardcoded auth.
- **Exactly one board per user** for MVP.
- **Board stored as JSON**.
- **DB created automatically if missing**.

## Proposed SQLite schema

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
```

## Board JSON shape

The JSON payload aligns with the existing frontend board types (`columns` + `cards`):

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"] },
    { "id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"] },
    { "id": "col-progress", "title": "In Progress", "cardIds": ["card-4"] },
    { "id": "col-review", "title": "Review", "cardIds": ["card-5"] },
    { "id": "col-done", "title": "Done", "cardIds": ["card-6"] }
  ],
  "cards": {
    "card-1": { "id": "card-1", "title": "Example task", "details": "Example details" }
  }
}
```

## Why this structure

### Keep board as one JSON document

Pros:
- simple CRUD for MVP
- naturally matches current frontend state shape
- easy to pass full board state to AI in later parts

Trade-off:
- write operations replace full board JSON, not row-level card updates

This trade-off is acceptable for MVP scale and one-board-per-user constraints.

### Separate users and boards tables

Pros:
- supports multiple users cleanly
- enforces one-board-per-user via `UNIQUE (user_id)`
- enables future auth migration without schema rewrite

## Initialization and migration approach (Part 6 implementation plan)

At backend startup:

1. Open SQLite DB file (proposed default: `backend/data/pm.db`).
2. Enable foreign keys: `PRAGMA foreign_keys = ON`.
3. Run `CREATE TABLE IF NOT EXISTS` statements in a transaction.
4. Ensure default MVP user row exists (`username = 'user'`).
5. Ensure that user has one board row:
   - if missing, create with default board JSON seeded from app defaults.

## Update strategy and consistency

- Reads return current `board_json` for a user.
- Writes replace `board_json` and increment `version`.
- `updated_at` is refreshed on each successful write.
- Optional optimistic concurrency can be added by requiring `version` match in update requests.

## Example operations this schema supports

- rename a column (update JSON, persist)
- add/edit/delete card (update JSON, persist)
- move card between columns (update JSON, persist)
- fetch board on page load (single read by user)

## Error handling expectations for Part 6

- if user is missing: return 404 (or create-on-read for MVP if explicitly chosen)
- if payload JSON is invalid shape: return 400 with clear message
- if DB unavailable: return 500 with explicit backend error response

## Test plan for Part 6 based on this schema

- DB file is created automatically when absent.
- Tables are created on startup.
- Default user row exists.
- Exactly one board row exists per user.
- Board writes persist across restart.
- Constraint checks:
  - duplicate username rejected
  - duplicate board for same user rejected
  - invalid JSON rejected by DB constraint

## Open implementation choices (recommendations)

1. **User lookup mode (recommended: by username)**
   - Use `username` as API identity key in MVP requests.
   - Keep internal FK on `user_id`.

2. **Write mode (recommended: replace full JSON)**
   - Keep implementation simple and aligned with current frontend state.

3. **DB path (recommended default)**
   - `backend/data/pm.db` within container/workspace.
