"""Shared tournament visibility rules for list and calendar endpoints."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.auth.roles import has_min_role, role_value as _role_value
from app.models import Player, User, UserRole


def role_value(user: User) -> str:
    return _role_value(user.role)


def is_staff_user(user: User | None) -> bool:
    return user is not None and has_min_role(user, UserRole.staff.value)


def is_public_list_event(event: dict) -> bool:
    status = event.get("status")
    if status == "finished":
        return True
    return status == "draft" and bool(event.get("registration_open"))


def is_public_calendar_event(event: dict) -> bool:
    """Pre-start and finished tournaments are visible on the public calendar.

    registration_open only controls online signup, not calendar visibility.
    """
    status = event.get("status")
    return status in {"draft", "finished"}


def registered_event_ids(db: Session, user_id: int) -> set[int]:
    rows = db.query(Player.event_id).filter(Player.user_id == user_id).all()
    return {int(r[0]) for r in rows}


def filter_calendar_tournaments(
    events: list[dict],
    viewer: User | None,
    db: Session,
) -> list[dict]:
    if is_staff_user(viewer):
        return events
    registered = registered_event_ids(db, viewer.id) if viewer is not None else set()
    return [
        e
        for e in events
        if is_public_calendar_event(e) or int(e["id"]) in registered
    ]
