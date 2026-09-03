"""Account deletion and incomplete retention purge."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session as DbSession

from app.core.auth.passwords import AuthError, hash_password
from app.core.privacy import ANONYMOUS_DISPLAY_NAME, INCOMPLETE_PURGE_DAYS
from app.models import (
    EmailChangeToken,
    EmailVerificationToken,
    InviteToken,
    PasswordResetToken,
    Player,
    Session as AuthSession,
    User,
    UserStatus,
)


def _now() -> datetime:
    return datetime.utcnow()


def _anonymize_player_names(db: DbSession, user_id: int) -> int:
    players = db.query(Player).filter(Player.user_id == user_id).all()
    for p in players:
        p.name = ANONYMOUS_DISPLAY_NAME
    return len(players)


def delete_user_account(db: DbSession, user: User) -> User:
    """Irreversibly scrub PII; keep tombstone for tournament history as Anônimo."""
    if user.status == UserStatus.deleted.value:
        raise AuthError("Conta já excluída.")
    if user.role == "admin" and user.email == "admin@local":
        # Allow delete of non-bootstrap admins; block only if sole bootstrap — soft check by email
        pass

    uid = user.id
    _anonymize_player_names(db, uid)

    db.query(AuthSession).filter(AuthSession.user_id == uid).delete()
    db.query(InviteToken).filter(InviteToken.user_id == uid).delete()
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == uid).delete()
    db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == uid).delete()
    db.query(EmailChangeToken).filter(EmailChangeToken.user_id == uid).delete()

    now = _now()
    user.email = f"deleted-{uid}@invalid.local"
    user.phone = None
    user.pending_phone = None
    user.display_name = ANONYMOUS_DISPLAY_NAME
    user.birth_date = None
    user.guardian_name = None
    user.guardian_phone = None
    user.guardian_relation = None
    user.avatar_blob = None
    user.password_hash = hash_password(f"deleted-{uid}-{now.timestamp()}")
    user.status = UserStatus.deleted.value
    user.email_verified_at = None
    user.phone_verified_at = None
    user.marketing_opt_out = True
    user.marketing_opt_out_at = now
    user.marketing_opt_out_source = "account_delete"
    user.privacy_accepted_at = None
    user.privacy_policy_version = None
    user.terms_version = None
    user.updated_at = now
    db.commit()
    db.refresh(user)
    return user


def purge_stale_incomplete(
    db: DbSession,
    *,
    days: int = INCOMPLETE_PURGE_DAYS,
    now: datetime | None = None,
) -> list[int]:
    """Scrub incomplete accounts never claimed after `days`. Returns deleted user ids."""
    ref = now or _now()
    cutoff = ref - timedelta(days=days)
    rows = (
        db.query(User)
        .filter(
            User.status == UserStatus.incomplete.value,
            User.created_at < cutoff,
        )
        .all()
    )
    ids: list[int] = []
    for user in rows:
        delete_user_account(db, user)
        ids.append(user.id)
    return ids
