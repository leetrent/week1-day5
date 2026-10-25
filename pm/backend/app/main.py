from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

app = FastAPI(title="PM MVP Backend", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def api_hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI backend"}


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
