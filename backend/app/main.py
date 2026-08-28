"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as api_v1_router
from app.config import get_settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


settings = get_settings()

app = FastAPI(title="TCG Tools", version="1.0.0", lifespan=lifespan)
app.include_router(api_v1_router)

dist = settings.resolved_frontend_dist
index_html = dist / "index.html"


if dist.exists() and index_html.exists():
    assets_dir = dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str) -> FileResponse:
        if full_path.startswith("api/") or full_path.startswith("media/"):
            from fastapi import HTTPException

            raise HTTPException(status_code=404)
        file_path = dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(index_html)

else:

    @app.get("/")
    async def root_placeholder() -> dict[str, str]:
        return {
            "message": "TCG Tools API",
            "docs": "/docs",
            "frontend": "Execute npm run build em frontend/",
        }
