"""Auth service: admin user + session cookies."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session as DbSession

from app.core.auth.passwords import (
    ADMIN_USERNAME,
    AuthError,
    hash_password,
    validate_password_plain,
    verify_password,
)
from app.models import Session as AuthSession
from app.models import User

SESSION_COOKIE = "tcgtools_session"
SESSION_DAYS = 7


def get_admin(db: DbSession) -> User | None:
    return db.query(User).filter(User.username == ADMIN_USERNAME).one_or_none()


def upsert_admin_password(db: DbSession, password: str) -> User:
    validate_password_plain(password)
    now = datetime.now(UTC).replace(tzinfo=None)
    user = get_admin(db)
    pwd_hash = hash_password(password)
    if user is None:
        user = User(username=ADMIN_USERNAME, password_hash=pwd_hash, created_at=now, updated_at=now)
        db.add(user)
    else:
        user.password_hash = pwd_hash
        user.updated_at = now
        db.query(AuthSession).filter(AuthSession.user_id == user.id).delete()
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: DbSession, username: str, password: str) -> User:
    if (username or "").strip().lower() != ADMIN_USERNAME:
        raise AuthError("Usuário ou senha inválidos.")
    user = get_admin(db)
    if user is None:
        raise AuthError(
            "Usuário admin ainda não foi configurado. Execute o instalador e defina a senha.",
        )
    if not verify_password(password, user.password_hash):
        raise AuthError("Usuário ou senha inválidos.")
    return user


def create_session(db: DbSession, user: User) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC).replace(tzinfo=None)
    row = AuthSession(
        token=token,
        user_id=user.id,
        created_at=now,
        expires_at=now + timedelta(days=SESSION_DAYS),
    )
    db.add(row)
    db.commit()
    return token


def get_user_for_token(db: DbSession, token: str | None) -> User | None:
    if not token:
        return None
    row = db.query(AuthSession).filter(AuthSession.token == token).one_or_none()
    if row is None:
        return None
    if row.expires_at < datetime.now(UTC).replace(tzinfo=None):
        db.delete(row)
        db.commit()
        return None
    return db.query(User).filter(User.id == row.user_id).one_or_none()


def revoke_session(db: DbSession, token: str | None) -> None:
    if not token:
        return
    db.query(AuthSession).filter(AuthSession.token == token).delete()
    db.commit()


def change_password(db: DbSession, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AuthError("Senha atual incorreta.")
    validate_password_plain(new_password)
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(UTC).replace(tzinfo=None)
    db.query(AuthSession).filter(AuthSession.user_id == user.id).delete()
    db.commit()
