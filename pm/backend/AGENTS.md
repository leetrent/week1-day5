# Backend notes

This folder contains the FastAPI backend scaffold for the Project Management MVP.

## Current contents

- `app/main.py`: FastAPI app entrypoint with:
  - `GET /` serving static hello-world HTML
  - `GET /health` healthcheck endpoint
  - `GET /api/hello` example JSON API endpoint
- `static/index.html`: minimal static page that calls `/api/hello`
- `pyproject.toml`: backend Python dependencies for `uv`-managed install

## Current purpose

This is scaffolding for Part 2 only. It validates local Dockerized startup and
basic backend/static serving before frontend and persistence integration.