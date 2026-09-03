"""Staff audit logging for sensitive actions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import StaffAuditLog, User


def client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return (request.client.host or "")[:64] or None
    return None


def log_staff_action(
    db: Session,
    *,
    actor: User | None,
    action: str,
    target_user_id: int | None = None,
    meta: dict[str, Any] | None = None,
    request: Request | None = None,
) -> StaffAuditLog:
    row = StaffAuditLog(
        actor_user_id=actor.id if actor is not None else None,
        action=action,
        target_user_id=target_user_id,
        meta=meta,
        ip=client_ip(request),
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
