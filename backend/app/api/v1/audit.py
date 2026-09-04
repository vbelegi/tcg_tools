"""Platform staff audit log listing (admin+)."""

from __future__ import annotations

from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin
from app.db.session import get_db
from app.models import StaffAuditLog, User

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(
    actor: RequireAdmin,
    db: Session = Depends(get_db),
    action: str | None = Query(default=None, max_length=64),
    actor_user_id: int | None = None,
    target_user_id: int | None = None,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    q = db.query(StaffAuditLog).order_by(StaffAuditLog.created_at.desc(), StaffAuditLog.id.desc())
    if action:
        q = q.filter(StaffAuditLog.action == action)
    if actor_user_id is not None:
        q = q.filter(StaffAuditLog.actor_user_id == actor_user_id)
    if target_user_id is not None:
        q = q.filter(StaffAuditLog.target_user_id == target_user_id)
    if from_date is not None:
        q = q.filter(StaffAuditLog.created_at >= datetime.combine(from_date, time.min))
    if to_date is not None:
        q = q.filter(StaffAuditLog.created_at <= datetime.combine(to_date, time.max))

    total = q.count()
    rows = q.offset(offset).limit(limit).all()

    actor_ids = {r.actor_user_id for r in rows if r.actor_user_id}
    target_ids = {r.target_user_id for r in rows if r.target_user_id}
    user_ids = actor_ids | target_ids
    names: dict[int, str] = {}
    if user_ids:
        for u in db.query(User).filter(User.id.in_(user_ids)).all():
            names[u.id] = u.display_name

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": r.id,
                "action": r.action,
                "actor_user_id": r.actor_user_id,
                "actor_display_name": names.get(r.actor_user_id) if r.actor_user_id else None,
                "target_user_id": r.target_user_id,
                "target_display_name": names.get(r.target_user_id) if r.target_user_id else None,
                "meta": r.meta,
                "ip": r.ip,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }
