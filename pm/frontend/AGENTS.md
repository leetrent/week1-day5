# Frontend agent notes

## Scope

This document describes the current state of the frontend in `frontend/` as it exists before backend and Docker integration work.

## Current stack

- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS v4
- dnd-kit (`@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`)
- Vitest + Testing Library for unit tests
- Playwright for end-to-end tests

## Current structure

- `src/app/`
  - `page.tsx`: renders the Kanban board as the homepage UI.
  - `layout.tsx`: root layout, metadata, and font wiring.
  - `globals.css`: design tokens and base global styles.
- `src/components/`
  - `KanbanBoard.tsx`: top-level board state and drag/drop orchestration.
  - `KanbanColumn.tsx`: column UI, title edit input, empty state, and add-card form mount.
  - `KanbanCard.tsx`: sortable card UI and remove button.
  - `KanbanCardPreview.tsx`: drag overlay preview.
  - `NewCardForm.tsx`: add-card form toggle and submit behavior.
- `src/lib/`
  - `kanban.ts`: board/card/column types, seed data, drag move logic, ID generation.
- `tests/`
  - `kanban.spec.ts`: Playwright flows for board load, add card, and drag between columns.
- `src/components/KanbanBoard.test.tsx`: unit tests for rendering, rename, add/remove card.
- `src/lib/kanban.test.ts`: unit tests for move logic.

## State management and data model

- All board state is in-memory React state inside `KanbanBoard`.
- Initial state is seeded from `initialData` in `src/lib/kanban.ts`.
- Data model:
  - `columns: Column[]` (ordered list of columns, each with ordered `cardIds`)
  - `cards: Record<string, Card>` (card entities keyed by id)
- There is no persistence layer and no API integration yet.
- Refreshing the page resets state to seed data.

## Current Kanban behavior

- Fixed five-column board is pre-populated from seed data.
- Column names are editable inline via input fields.
- Cards can be moved:
  - within a column (reorder)
  - between columns
  - to the end of a column by dropping on the column container
- Cards can be created in a specific column via `NewCardForm`.
- Cards can be removed from a column.
- Drag interaction uses pointer sensor activation distance and a card overlay preview.

## Current AI chat behavior

- There is no AI chat sidebar or chat UI in the current frontend implementation.
- There are no frontend calls to backend AI endpoints.
- AI-assisted card operations are not implemented yet.

## Styling and design notes

- Uses CSS variables in `globals.css` for color and surface tokens.
- Current colors align with project palette:
  - Accent yellow `#ecad0a`
  - Primary blue `#209dd7`
  - Secondary purple `#753991`
  - Dark navy `#032147`
  - Gray text `#888888`

## Testing status

- Unit tests cover:
  - board rendering
  - column rename behavior
  - add/remove card flow
  - card movement logic
- E2E tests cover:
  - initial board load
  - adding a card
  - moving a card between columns

## Known limitations and assumptions

- Frontend-only demo with no authentication.
- No backend integration, no data persistence, no multi-user behavior.
- No AI chat surface or structured AI update flow.
- Board structure is seeded and fixed to one board view in UI.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
