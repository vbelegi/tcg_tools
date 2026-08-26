"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import SESSION_COOKIE, get_user_for_token
from app.db.session import get_db
from app.models import User, UserRole

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


def require_roles(*roles: str) -> Callable[..., User]:
    allowed = set(roles)

    def _dep(user: User = Depends(get_current_user)) -> User:
        role = user.role.value if hasattr(user.role, "value") else str(user.role)
        if role not in allowed:
            raise HTTPException(status_code=403, detail="Permissão insuficiente.")
        return user

    return _dep


require_admin = require_roles(UserRole.admin.value)
require_staff = require_roles(UserRole.admin.value, UserRole.staff.value)
require_player = require_roles(
    UserRole.admin.value, UserRole.staff.value, UserRole.player.value
)

RequireAdmin = Annotated[User, Depends(require_admin)]
RequireStaff = Annotated[User, Depends(require_staff)]
RequirePlayer = Annotated[User, Depends(require_player)]
