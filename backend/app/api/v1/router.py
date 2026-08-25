"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, health, premiacao, torneios

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(premiacao.router)
router.include_router(torneios.router)
