"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import SESSION_COOKIE, get_user_for_token
from app.db.session import get_db
from app.models import User

DbDep = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: Session = Depends(get_db),
    tcgtools_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> User:
    user = get_user_for_token(db, tcgtools_session)
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    return user


def get_optional_user(
    db: Session = Depends(get_db),
    tcgtools_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> User | None:
    return get_user_for_token(db, tcgtools_session)
