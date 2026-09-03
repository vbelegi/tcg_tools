"""Transactional notices to promotional-action participants."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.core.email.outbound import send_promo_update_email
from app.models import PromoAction, PromoParticipant

logger = logging.getLogger(__name__)


def _fmt_date(value: date | str | None) -> str:
    if value is None:
        return "—"
    iso = value.isoformat() if isinstance(value, date) else str(value)
    parts = iso.split("-")
    if len(parts) == 3:
        return "/".join(reversed(parts))
    return iso


def _fmt_limit(value: int | None) -> str:
    return "sem limite" if value is None else str(value)


def describe_edit_changes(changes: dict, action: PromoAction) -> list[str]:
    lines: list[str] = []
    if "name" in changes:
        lines.append(f"Nome: {changes['name']['from']} → {changes['name']['to']}")
    if "start_date" in changes or "end_date" in changes:
        lines.append(f"Período: {_fmt_date(action.start_date)} a {_fmt_date(action.end_date)}")
    if "description" in changes:
        lines.append("A descrição foi atualizada.")
    if "max_participants" in changes:
        lines.append(
            "Limite de participantes: "
            f"{_fmt_limit(changes['max_participants']['from'])} → "
            f"{_fmt_limit(changes['max_participants']['to'])}"
        )
    if "show_in_calendar" in changes:
        showing = bool(changes["show_in_calendar"]["to"])
        lines.append(
            "A ação passou a aparecer no calendário."
            if showing
            else "A ação saiu do calendário."
        )
    return lines


def notify_promo_participants(db: Session, action: PromoAction, change_lines: list[str]) -> int:
    """Send a transactional update to every enrolled user with an e-mail. Returns sent count."""
    if not change_lines:
        return 0
    rows = (
        db.query(PromoParticipant)
        .options(joinedload(PromoParticipant.user))
        .filter(PromoParticipant.promo_id == action.id)
        .all()
    )
    sent = 0
    for row in rows:
        user = row.user
        if user is None or not (user.email or "").strip():
            continue
        try:
            send_promo_update_email(
                user,
                action_name=action.name,
                action_id=action.id,
                change_lines=change_lines,
            )
            sent += 1
        except Exception:
            logger.exception("Failed to notify promo participant user_id=%s promo_id=%s", user.id, action.id)
    return sent
