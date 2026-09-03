"""One-shot draw for a promotional action.

The pool is confirmed participants only. Direct mode is drawn on the server;
chained mode persists the ordered list the staff confirmed after picking one
by one. A second draw always fails.
"""

from __future__ import annotations

import secrets
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.promo.enrollment import action_has_ended, get_participation
from app.models import (
    PromoAction,
    PromoDrawMode,
    PromoDrawResult,
    PromoParticipant,
    PromoParticipantStatus,
    User,
)

MSG_TOO_EARLY = "O sorteio só pode ser realizado após o término da ação."
MSG_ALREADY = "O sorteio desta ação já foi realizado."
MSG_NO_POOL = "Não há participantes confirmados para o sorteio."
MSG_NOT_DONE = "O sorteio ainda não foi realizado."
MSG_BAD_COUNT = "Informe pelo menos 1 sorteado, até o tamanho da pool confirmada."
MSG_BAD_IDS = "A lista de contemplados precisa ser um subconjunto da pool confirmada, sem repetição."
MSG_BAD_MODE = "Modo de sorteio inválido."


class DrawError(ValueError):
    def __init__(self, message: str, *, status_code: int = 400):
        self.status_code = status_code
        super().__init__(message)


def get_draw(db: Session, promo_id: int) -> PromoDrawResult | None:
    return db.query(PromoDrawResult).filter(PromoDrawResult.promo_id == promo_id).one_or_none()


def confirmed_user_ids(db: Session, promo_id: int) -> list[int]:
    rows = (
        db.query(PromoParticipant.user_id)
        .filter(
            PromoParticipant.promo_id == promo_id,
            PromoParticipant.status == PromoParticipantStatus.confirmed.value,
        )
        .order_by(PromoParticipant.registered_at.asc(), PromoParticipant.id.asc())
        .all()
    )
    return [int(user_id) for (user_id,) in rows]


def _require_ended_and_fresh(db: Session, action: PromoAction) -> None:
    if not action_has_ended(action):
        raise DrawError(MSG_TOO_EARLY, status_code=400)
    if get_draw(db, action.id) is not None:
        raise DrawError(MSG_ALREADY, status_code=409)


def persist_draw(
    db: Session,
    action: PromoAction,
    *,
    mode: str,
    winner_count: int | None,
    winner_user_ids: list[int] | None,
    actor: User,
) -> PromoDrawResult:
    _require_ended_and_fresh(db, action)
    pool = confirmed_user_ids(db, action.id)
    if not pool:
        raise DrawError(MSG_NO_POOL, status_code=400)

    if mode == PromoDrawMode.direct.value:
        if winner_count is None or winner_count < 1 or winner_count > len(pool):
            raise DrawError(MSG_BAD_COUNT, status_code=400)
        chosen = secrets.SystemRandom().sample(pool, winner_count)
    elif mode == PromoDrawMode.chained.value:
        chosen = list(winner_user_ids or [])
        if not chosen or len(chosen) != len(set(chosen)):
            raise DrawError(MSG_BAD_IDS, status_code=400)
        allowed = set(pool)
        if any(user_id not in allowed for user_id in chosen):
            raise DrawError(MSG_BAD_IDS, status_code=400)
    else:
        raise DrawError(MSG_BAD_MODE, status_code=400)

    row = PromoDrawResult(
        promo_id=action.id,
        drawn_at=datetime.utcnow(),
        drawn_by_user_id=actor.id,
        mode=mode,
        winner_count=len(chosen),
        winner_user_ids=chosen,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DrawError(MSG_ALREADY, status_code=409) from exc
    db.refresh(row)
    return row


def viewer_draw_fields(
    db: Session, action: PromoAction, viewer: User | None
) -> tuple[bool, bool | None]:
    """Logged-in: whether a draw exists, and if this viewer won. Guests get (False, None)."""
    if viewer is None:
        return False, None
    draw = get_draw(db, action.id)
    if draw is None:
        return False, None
    mine = get_participation(db, action.id, viewer.id)
    if mine is None:
        return True, None
    return True, int(viewer.id) in {int(uid) for uid in (draw.winner_user_ids or [])}


def winner_rows(db: Session, draw: PromoDrawResult) -> list[User]:
    ids = [int(uid) for uid in (draw.winner_user_ids or [])]
    if not ids:
        return []
    users = {
        user.id: user
        for user in db.query(User).filter(User.id.in_(ids)).all()
    }
    return [users[uid] for uid in ids if uid in users]
