"""Single-use QR enrolment for promotional actions.

The raw QR token dies on first access. A guest gets a 10-minute HttpOnly cookie
tied to that access so they can finish login/register in the store; anyone else
who opens the same link sees it as already used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth.session_tokens import generate_session_token, hash_session_token, verify_session_token
from app.core.promo.eligibility import is_account_contactable
from app.models import (
    PromoAction,
    PromoEnrollmentToken,
    PromoParticipant,
    PromoParticipantStatus,
    User,
)

ENROLL_TTL = timedelta(minutes=10)
ENROLL_COOKIE = "promo_enroll"

REASON_OK = "ok"
REASON_NEEDS_AUTH = "needs_auth"
REASON_NEEDS_VERIFICATION = "needs_verification"
REASON_ALREADY_ENROLLED = "already_enrolled"
REASON_FULL = "full"
REASON_ENDED = "ended"
REASON_EXPIRED = "expired"
REASON_USED = "used"
REASON_INVALID = "invalid"

MESSAGES: dict[str, str] = {
    REASON_OK: "Inscrição confirmada.",
    REASON_NEEDS_AUTH: "Entre ou crie uma conta para concluir a inscrição.",
    REASON_NEEDS_VERIFICATION: "Inscrição pendente; confirme seu e-mail.",
    REASON_ALREADY_ENROLLED: "Você já está inscrito nesta ação.",
    REASON_FULL: "Limite de participantes atingido.",
    REASON_ENDED: "A ação já foi encerrada.",
    REASON_EXPIRED: "Link expirado (validade de 10 minutos). Peça um novo QR ao atendente.",
    REASON_USED: "Este link já foi utilizado.",
    REASON_INVALID: "Link inválido.",
}

HTTP_STATUS: dict[str, int] = {
    REASON_OK: 200,
    REASON_NEEDS_AUTH: 200,
    REASON_NEEDS_VERIFICATION: 200,
    REASON_ALREADY_ENROLLED: 409,
    REASON_FULL: 409,
    REASON_ENDED: 400,
    REASON_EXPIRED: 400,
    REASON_USED: 400,
    REASON_INVALID: 400,
}


class EnrollmentError(ValueError):
    def __init__(self, reason: str, message: str | None = None):
        self.reason = reason
        super().__init__(message or MESSAGES[reason])


@dataclass
class EnrollResult:
    reason: str
    message: str
    action_id: int | None = None
    action_name: str | None = None
    participation_status: str | None = None
    set_cookie: str | None = None
    clear_cookie: bool = False
    cookie_max_age: int | None = None

    @property
    def http_status(self) -> int:
        return HTTP_STATUS[self.reason]

    def as_dict(self) -> dict:
        return {
            "reason": self.reason,
            "message": self.message,
            "action_id": self.action_id,
            "action_name": self.action_name,
            "participation_status": self.participation_status,
        }


def _now() -> datetime:
    return datetime.utcnow()


def _result(reason: str, action: PromoAction | None = None, status: str | None = None) -> EnrollResult:
    return EnrollResult(
        reason=reason,
        message=MESSAGES[reason],
        action_id=action.id if action is not None else None,
        action_name=action.name if action is not None else None,
        participation_status=status,
    )


def _seconds_left(expires_at: datetime, now: datetime | None = None) -> int:
    remaining = int((expires_at - (now or _now())).total_seconds())
    return max(remaining, 0)


def participant_count(db: Session, promo_id: int) -> int:
    return db.query(PromoParticipant).filter(PromoParticipant.promo_id == promo_id).count()


def get_participation(db: Session, promo_id: int, user_id: int) -> PromoParticipant | None:
    return (
        db.query(PromoParticipant)
        .filter(PromoParticipant.promo_id == promo_id, PromoParticipant.user_id == user_id)
        .one_or_none()
    )


def action_has_ended(action: PromoAction, today=None) -> bool:
    from datetime import date as date_cls

    return action.end_date < (today or date_cls.today())


def action_is_full(db: Session, action: PromoAction) -> bool:
    if action.max_participants is None:
        return False
    return participant_count(db, action.id) >= action.max_participants


def create_enrollment_token(
    db: Session, action: PromoAction, actor: User
) -> tuple[str, PromoEnrollmentToken]:
    if action_has_ended(action):
        raise EnrollmentError(REASON_ENDED)
    if action_is_full(db, action):
        raise EnrollmentError(REASON_FULL)
    now = _now()
    raw = generate_session_token()
    row = PromoEnrollmentToken(
        token=hash_session_token(raw),
        promo_id=action.id,
        created_by_user_id=actor.id,
        created_at=now,
        expires_at=now + ENROLL_TTL,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return raw, row


def _enroll_user(
    db: Session,
    action: PromoAction,
    user: User,
    *,
    existing_is_ok: bool = False,
) -> EnrollResult:
    existing = get_participation(db, action.id, user.id)
    if existing is not None:
        if existing_is_ok:
            reason = (
                REASON_OK
                if existing.status == PromoParticipantStatus.confirmed.value
                else REASON_NEEDS_VERIFICATION
            )
            result = _result(reason, action, existing.status)
            result.clear_cookie = True
            return result
        result = _result(REASON_ALREADY_ENROLLED, action, existing.status)
        result.clear_cookie = True
        return result
    if action_has_ended(action):
        return _result(REASON_ENDED, action)
    if action_is_full(db, action):
        return _result(REASON_FULL, action)

    status = (
        PromoParticipantStatus.confirmed.value
        if is_account_contactable(user)
        else PromoParticipantStatus.pending_verification.value
    )
    db.add(
        PromoParticipant(
            promo_id=action.id,
            user_id=user.id,
            status=status,
            registered_at=_now(),
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = get_participation(db, action.id, user.id)
        result = _result(REASON_ALREADY_ENROLLED, action, existing.status if existing else None)
        result.clear_cookie = True
        return result

    reason = REASON_OK if status == PromoParticipantStatus.confirmed.value else REASON_NEEDS_VERIFICATION
    result = _result(reason, action, status)
    result.clear_cookie = True
    return result


def consume_token(
    db: Session,
    raw_token: str,
    viewer: User | None,
    pending_cookie: str | None,
) -> EnrollResult:
    token_hash = hash_session_token(raw_token)
    row = db.query(PromoEnrollmentToken).filter(PromoEnrollmentToken.token == token_hash).one_or_none()
    if row is None:
        return _result(REASON_INVALID)

    action = db.query(PromoAction).filter(PromoAction.id == row.promo_id).one_or_none()
    now = _now()

    if row.used_at is not None:
        cookie_ok = bool(
            pending_cookie
            and row.pending_session_hash
            and verify_session_token(pending_cookie, row.pending_session_hash)
        )
        if cookie_ok and row.expires_at >= now:
            if viewer is not None:
                return (
                    _enroll_user(db, action, viewer, existing_is_ok=True)
                    if action
                    else _result(REASON_INVALID)
                )
            replay = _result(REASON_NEEDS_AUTH, action)
            replay.set_cookie = pending_cookie
            replay.cookie_max_age = _seconds_left(row.expires_at, now)
            return replay
        return _result(REASON_USED, action)

    if row.expires_at < now:
        return _result(REASON_EXPIRED, action)

    # First access: the QR dies here even if enrolment cannot finish.
    row.used_at = now
    db.flush()

    if action is None:
        db.commit()
        return _result(REASON_INVALID)

    if action_has_ended(action):
        db.commit()
        return _result(REASON_ENDED, action)

    if viewer is not None:
        db.commit()
        return _enroll_user(db, action, viewer)

    if action_is_full(db, action):
        db.commit()
        return _result(REASON_FULL, action)

    pending_raw = generate_session_token()
    row.pending_session_hash = hash_session_token(pending_raw)
    db.commit()
    result = _result(REASON_NEEDS_AUTH, action)
    result.set_cookie = pending_raw
    result.cookie_max_age = _seconds_left(row.expires_at, now)
    return result


def complete_enrollment(
    db: Session,
    viewer: User | None,
    pending_cookie: str | None,
) -> EnrollResult:
    if not pending_cookie:
        return _result(REASON_INVALID)
    cookie_hash = hash_session_token(pending_cookie)
    row = (
        db.query(PromoEnrollmentToken)
        .filter(PromoEnrollmentToken.pending_session_hash == cookie_hash)
        .one_or_none()
    )
    if row is None:
        return _result(REASON_INVALID)

    action = db.query(PromoAction).filter(PromoAction.id == row.promo_id).one_or_none()
    now = _now()
    if row.expires_at < now:
        result = _result(REASON_EXPIRED, action)
        result.clear_cookie = True
        return result
    if viewer is None:
        return _result(REASON_NEEDS_AUTH, action)
    if action is None:
        result = _result(REASON_INVALID)
        result.clear_cookie = True
        return result
    return _enroll_user(db, action, viewer, existing_is_ok=True)


def promote_pending_on_verify(db: Session, user: User) -> int:
    updated = (
        db.query(PromoParticipant)
        .filter(
            PromoParticipant.user_id == user.id,
            PromoParticipant.status == PromoParticipantStatus.pending_verification.value,
        )
        .update(
            {PromoParticipant.status: PromoParticipantStatus.confirmed.value},
            synchronize_session=False,
        )
    )
    db.commit()
    return int(updated or 0)
