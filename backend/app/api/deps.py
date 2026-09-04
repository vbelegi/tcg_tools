"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import SESSION_COOKIE, get_user_for_token
from app.core.auth.roles import ROLE_LEVEL, has_min_role, role_value
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


def require_min_role(minimum: str) -> Callable[..., User]:
    if minimum not in ROLE_LEVEL:
        raise ValueError(f"Unknown role: {minimum}")

    def _dep(user: User = Depends(get_current_user)) -> User:
        if not has_min_role(user, minimum):
            raise HTTPException(status_code=403, detail="Permissão insuficiente.")
        return user

    return _dep


def require_roles(*roles: str) -> Callable[..., User]:
    """Exact-role check (legacy). Prefer require_min_role for hierarchy."""
    allowed = set(roles)

    def _dep(user: User = Depends(get_current_user)) -> User:
        if role_value(user.role) not in allowed:
            raise HTTPException(status_code=403, detail="Permissão insuficiente.")
        return user

    return _dep


require_superadmin = require_min_role(UserRole.superadmin.value)
require_admin = require_min_role(UserRole.admin.value)
require_staff = require_min_role(UserRole.staff.value)
require_player = require_min_role(UserRole.player.value)

RequireSuperadmin = Annotated[User, Depends(require_superadmin)]
RequireAdmin = Annotated[User, Depends(require_admin)]
RequireStaff = Annotated[User, Depends(require_staff)]
RequirePlayer = Annotated[User, Depends(require_player)]
