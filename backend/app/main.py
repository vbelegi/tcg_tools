"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as api_v1_router
from app.config import get_settings
from app.db.init_db import init_db
from app.middleware.body_limit import MaxBodySizeMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="TCG Tools",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)
app.add_middleware(MaxBodySizeMiddleware, max_bytes=settings.max_request_body_bytes)
app.include_router(api_v1_router)

dist = settings.resolved_frontend_dist
index_html = dist / "index.html"


def _safe_dist_file(full_path: str) -> Path | None:
    if not full_path or full_path.startswith(("/", "\\")):
        return None
    candidate = (dist / full_path).resolve()
    try:
        candidate.relative_to(dist.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


if dist.exists() and index_html.exists():
    assets_dir = dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str) -> FileResponse:
        if full_path.startswith("api/") or full_path.startswith("media/"):
            raise HTTPException(status_code=404)
        safe = _safe_dist_file(full_path)
        if safe is not None:
            return FileResponse(safe)
        return FileResponse(index_html)

else:

    @app.get("/")
    async def root_placeholder() -> dict[str, str]:
        return {
            "message": "TCG Tools API",
            "docs": "/docs",
            "frontend": "Execute npm run build em frontend/",
        }
