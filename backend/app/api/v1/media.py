"""Serve user avatars stored in the database."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User

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
