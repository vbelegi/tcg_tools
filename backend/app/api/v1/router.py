"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, calendar, health, media, premiacao, tcg_games, torneios, users

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(media.router)
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(calendar.router)
router.include_router(tcg_games.router)
router.include_router(premiacao.router)
router.include_router(torneios.router)
