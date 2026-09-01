"""Auth service: sessions, login by email, admin bootstrap."""

from __future__ import annotations

import secrets
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session as DbSession

from app.core.auth.passwords import (
    ADMIN_EMAIL,
    AuthError,
    hash_password,
    normalize_email,
    normalize_phone,
    validate_password_plain,
    verify_password,
)
from app.core.auth.session_tokens import generate_session_token, hash_session_token
from app.models import (
    InviteToken,
    PasswordResetToken,
    Session as AuthSession,
    User,
    UserRole,
    UserStatus,
)

SESSION_COOKIE = "tcgtools_session"
SESSION_DAYS = 7
INVITE_DAYS = 7
PASSWORD_RESET_DAYS = 2


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def get_user_by_email(db: DbSession, email: str) -> User | None:
    return db.query(User).filter(User.email == normalize_email(email)).one_or_none()


def get_admin(db: DbSession) -> User | None:
    return (
        db.query(User)
        .filter(User.role == UserRole.admin.value)
        .order_by(User.id.asc())
        .first()
    )


def upsert_admin_password(db: DbSession, password: str) -> User:
    """Installer/bootstrap: ensure an active admin with the given password."""
    validate_password_plain(password)
    now = _now()
    pwd_hash = hash_password(password)
    user = get_user_by_email(db, ADMIN_EMAIL)
    if user is None:
        # Legacy username=admin row from migration 004
        user = db.query(User).filter(User.username == "admin").one_or_none()
    if user is None:
        user = User(
            email=ADMIN_EMAIL,
            display_name="Admin",
            username="admin",
            role=UserRole.admin.value,
            status=UserStatus.active.value,
            password_hash=pwd_hash,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
    else:
        user.email = ADMIN_EMAIL
        user.display_name = user.display_name or "Admin"
        user.role = UserRole.admin.value
        user.status = UserStatus.active.value
        user.password_hash = pwd_hash
        user.updated_at = now
        db.query(AuthSession).filter(AuthSession.user_id == user.id).delete()
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: DbSession, email: str, password: str) -> User:
    raw = (email or "").strip()
    try:
        normalized = ADMIN_EMAIL if raw.lower() == "admin" else normalize_email(raw)
    except AuthError as exc:
        raise AuthError("E-mail ou senha inválidos.") from exc
    user = get_user_by_email(db, normalized)
    if user is None and normalized == ADMIN_EMAIL:
        user = db.query(User).filter(User.username == "admin").one_or_none() or get_admin(db)
    if user is None:
        raise AuthError("E-mail ou senha inválidos.")
    if user.status != UserStatus.active.value:
        raise AuthError("Conta ainda não finalizada. Use o link de convite.")
    if not verify_password(password, user.password_hash):
        raise AuthError("E-mail ou senha inválidos.")
    return user


def create_session(db: DbSession, user: User) -> str:
    db.query(AuthSession).filter(AuthSession.user_id == user.id).delete()
    token = generate_session_token()
    now = _now()
    row = AuthSession(
        token=hash_session_token(token),
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
    token_hash = hash_session_token(token)
    row = db.query(AuthSession).filter(AuthSession.token == token_hash).one_or_none()
    if row is None:
        return None
    if row.expires_at < _now():
        db.delete(row)
        db.commit()
        return None
    user = db.query(User).filter(User.id == row.user_id).one_or_none()
    if user is None or user.status != UserStatus.active.value:
        return None
    return user


def revoke_session(db: DbSession, token: str | None) -> None:
    if not token:
        return
    db.query(AuthSession).filter(AuthSession.token == hash_session_token(token)).delete()
    db.commit()


def change_password(db: DbSession, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AuthError("Senha atual incorreta.")
    validate_password_plain(new_password)
    user.password_hash = hash_password(new_password)
    user.updated_at = _now()
    db.query(AuthSession).filter(AuthSession.user_id == user.id).delete()
    db.commit()


def ensure_unique_email_phone(
    db: DbSession,
    *,
    email: str,
    phone: str | None,
    exclude_user_id: int | None = None,
) -> tuple[str, str | None]:
    email_n = normalize_email(email)
    phone_n = normalize_phone(phone) if phone else None
    q = db.query(User).filter(User.email == email_n)
    if exclude_user_id is not None:
        q = q.filter(User.id != exclude_user_id)
    if q.one_or_none():
        raise AuthError("Já existe uma conta com este e-mail.")
    if phone_n:
        q2 = db.query(User).filter(User.phone == phone_n)
        if exclude_user_id is not None:
            q2 = q2.filter(User.id != exclude_user_id)
        if q2.one_or_none():
            raise AuthError("Já existe uma conta com este celular.")
    return email_n, phone_n


def age_years(birth: date, today: date | None = None) -> int:
    today = today or date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def require_guardian_if_minor(
    birth_date: date | None,
    guardian_name: str | None,
    guardian_phone: str | None,
) -> None:
    if birth_date is None:
        raise AuthError("Data de nascimento é obrigatória.")
    if age_years(birth_date) >= 18:
        return
    if not (guardian_name or "").strip() or not (guardian_phone or "").strip():
        raise AuthError("Menores de 18 anos precisam dos dados do responsável.")


def create_incomplete_user(
    db: DbSession,
    *,
    display_name: str,
    email: str,
    phone: str,
    role: str = UserRole.player.value,
    birth_date: date | None = None,
    guardian_name: str | None = None,
    guardian_phone: str | None = None,
    guardian_relation: str | None = None,
) -> User:
    name = (display_name or "").strip()
    if not name:
        raise AuthError("Nome de exibição é obrigatório.")
    email_n, phone_n = ensure_unique_email_phone(db, email=email, phone=phone)
    assert phone_n is not None
    now = _now()
    user = User(
        email=email_n,
        display_name=name,
        phone=phone_n,
        role=role,
        status=UserStatus.incomplete.value,
        password_hash=None,
        birth_date=birth_date,
        guardian_name=guardian_name,
        guardian_phone=guardian_phone,
        guardian_relation=guardian_relation,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register_player(
    db: DbSession,
    *,
    display_name: str,
    email: str,
    phone: str,
    password: str,
    birth_date: date,
    guardian_name: str | None = None,
    guardian_phone: str | None = None,
    guardian_relation: str | None = None,
) -> User:
    """Public self-signup: creates an active player with password."""
    name = (display_name or "").strip()
    if not name:
        raise AuthError("Nome de exibição é obrigatório.")
    validate_password_plain(password)
    email_n, phone_n = ensure_unique_email_phone(db, email=email, phone=phone)
    if not phone_n:
        raise AuthError("Celular é obrigatório.")
    require_guardian_if_minor(birth_date, guardian_name, guardian_phone)
    now = _now()
    user = User(
        email=email_n,
        display_name=name,
        phone=phone_n,
        role=UserRole.player.value,
        status=UserStatus.active.value,
        password_hash=hash_password(password),
        birth_date=birth_date,
        guardian_name=(guardian_name or "").strip() or None,
        guardian_phone=(guardian_phone or "").strip() or None,
        guardian_relation=(guardian_relation or "").strip() or None,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_invite(db: DbSession, user: User) -> InviteToken:
    if user.status == UserStatus.active.value:
        raise AuthError("Conta já está ativa.")
    now = _now()
    db.query(InviteToken).filter(
        InviteToken.user_id == user.id,
        InviteToken.used_at.is_(None),
    ).delete()
    token = secrets.token_urlsafe(32)
    row = InviteToken(
        token=token,
        user_id=user.id,
        created_at=now,
        expires_at=now + timedelta(days=INVITE_DAYS),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def claim_invite(
    db: DbSession,
    token: str,
    password: str,
    *,
    birth_date: date,
    guardian_name: str | None = None,
    guardian_phone: str | None = None,
    guardian_relation: str | None = None,
) -> User:
    row = db.query(InviteToken).filter(InviteToken.token == token).one_or_none()
    if row is None or row.used_at is not None:
        raise AuthError("Convite inválido ou já utilizado.")
    if row.expires_at < _now():
        raise AuthError("Convite expirado.")
    user = db.query(User).filter(User.id == row.user_id).one()
    validate_password_plain(password)
    user.password_hash = hash_password(password)
    user.status = UserStatus.active.value
    user.birth_date = birth_date
    if guardian_name is not None:
        user.guardian_name = guardian_name.strip() or None
    if guardian_phone is not None:
        user.guardian_phone = guardian_phone.strip() or None
    if guardian_relation is not None:
        user.guardian_relation = guardian_relation.strip() or None
    require_guardian_if_minor(user.birth_date, user.guardian_name, user.guardian_phone)
    user.updated_at = _now()
    row.used_at = _now()
    db.commit()
    db.refresh(user)
    return user


def create_password_reset(db: DbSession, user: User) -> tuple[str, PasswordResetToken]:
    if user.status != UserStatus.active.value:
        raise AuthError("Só é possível resetar senha de contas ativas.")
    now = _now()
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).delete()
    db.query(AuthSession).filter(AuthSession.user_id == user.id).delete()
    raw = generate_session_token()
    row = PasswordResetToken(
        token=hash_session_token(raw),
        user_id=user.id,
        created_at=now,
        expires_at=now + timedelta(days=PASSWORD_RESET_DAYS),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return raw, row


def claim_password_reset(db: DbSession, token: str, password: str) -> User:
    token_hash = hash_session_token(token)
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token == token_hash).one_or_none()
    if row is None or row.used_at is not None:
        raise AuthError("Link inválido ou já utilizado.")
    if row.expires_at < _now():
        raise AuthError("Link expirado.")
    user = db.query(User).filter(User.id == row.user_id).one()
    if user.status != UserStatus.active.value:
        raise AuthError("Conta não está ativa.")
    validate_password_plain(password)
    user.password_hash = hash_password(password)
    user.updated_at = _now()
    row.used_at = _now()
    db.query(AuthSession).filter(AuthSession.user_id == user.id).delete()
    db.commit()
    db.refresh(user)
    return user


def public_user_dict(user: User) -> dict:
    from app.core.auth.avatars import user_avatar_url

    return {
        "id": user.id,
        "display_name": user.display_name,
        "role": user.role,
        "status": user.status,
        "avatar_url": user_avatar_url(user.id, user.avatar_blob),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def private_user_dict(user: User) -> dict:
    return {
        **public_user_dict(user),
        "email": user.email,
        "phone": user.phone,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
        "guardian_name": user.guardian_name,
        "guardian_phone": user.guardian_phone,
        "guardian_relation": user.guardian_relation,
    }
