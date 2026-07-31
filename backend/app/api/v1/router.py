"""API v1 router.

Auth futura: usar dependency `get_current_user` de `app.api.deps` (stub retorna None na v1).
"""

from fastapi import APIRouter

from app.api.v1 import health, premiacao, torneios

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(premiacao.router)
router.include_router(torneios.router)
