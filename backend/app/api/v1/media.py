"""Serve user avatars stored in the database and promotional regulation PDFs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import RequireStaff, get_optional_user
from app.api.v1.promo_visibility import can_view_promo
from app.core.promo import regulations
from app.db.session import get_db
from app.models import PromoAction, PromoRegulationVersion, User

router = APIRouter(tags=["media"])


@router.get("/media/avatars/{user_id}")
def get_user_avatar(user_id: int, db: Session = Depends(get_db)) -> Response:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None or not user.avatar_blob:
        raise HTTPException(status_code=404, detail="Avatar não encontrado.")
    return Response(
        content=user.avatar_blob,
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=86400"},
    )


def _regulation_response(action: PromoAction, row: PromoRegulationVersion) -> FileResponse:
    path = regulations.regulation_path(action.id, row.stored_name)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Regulamento não encontrado.")
    filename = regulations.download_filename(action, row.version)
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/media/acoes/{action_id}/regulamento")
def get_current_regulation(
    action_id: int,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
) -> FileResponse:
    action = db.query(PromoAction).filter(PromoAction.id == action_id).one_or_none()
    if action is None or not can_view_promo(action, viewer):
        raise HTTPException(status_code=404, detail="Ação não encontrada.")
    if not action.regulation_version:
        raise HTTPException(status_code=404, detail="Regulamento não encontrado.")
    row = regulations.get_version(db, action.id, action.regulation_version)
    if row is None:
        raise HTTPException(status_code=404, detail="Regulamento não encontrado.")
    return _regulation_response(action, row)


@router.get("/media/acoes/{action_id}/regulamento/{version}")
def get_regulation_version(
    action_id: int,
    version: int,
    _: RequireStaff,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Superseded versions stay available to staff for audit."""
    action = db.query(PromoAction).filter(PromoAction.id == action_id).one_or_none()
    if action is None:
        raise HTTPException(status_code=404, detail="Ação não encontrada.")
    row = regulations.get_version(db, action.id, version)
    if row is None:
        raise HTTPException(status_code=404, detail="Regulamento não encontrado.")
    return _regulation_response(action, row)
