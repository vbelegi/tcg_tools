"""Public calendar feed and staff CRUD for non-tournament announcements."""

from __future__ import annotations

import re
from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import RequireStaff, get_optional_user
from app.api.v1.event_visibility import filter_calendar_tournaments
from app.api.v1.promo_visibility import promo_public_cutoff
from app.core.promo.types import get_handler
from app.db.session import get_db
from app.models import CalendarAnnouncement, PromoAction, User
from app.services.torneio_service import TorneioService

router = APIRouter(tags=["calendar"])

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def get_torneio_service(db: Session = Depends(get_db)) -> TorneioService:
    return TorneioService(db)


def _announcement_dict(row: CalendarAnnouncement) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "event_date": row.event_date.isoformat(),
        "description": row.description,
        "start_time": row.start_time,
        "location": row.location,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "created_by_user_id": row.created_by_user_id,
    }


def _promo_calendar_dict(row: PromoAction) -> dict:
    handler = get_handler(row.type)
    return {
        "id": row.id,
        "name": row.name,
        "start_date": row.start_date.isoformat(),
        "end_date": row.end_date.isoformat(),
        "description": row.description,
        "type_label": handler.label if handler else row.type,
    }


def _validate_time(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    clean = value.strip()
    if not _TIME_RE.match(clean):
        raise HTTPException(status_code=422, detail="Horário inválido. Use HH:MM (24h).")
    return clean


class AnnouncementBody(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    event_date: date
    description: str | None = None
    start_time: str | None = Field(default=None, max_length=5)
    location: str | None = Field(default=None, max_length=200)


class AnnouncementPatchBody(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    event_date: date | None = None
    description: str | None = None
    start_time: str | None = Field(default=None, max_length=5)
    location: str | None = Field(default=None, max_length=200)


@router.get("/calendar")
def calendar_month(
    year: int,
    month: int,
    svc: TorneioService = Depends(get_torneio_service),
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=422, detail="Mês inválido.")
    if year < 2000 or year > 2100:
        raise HTTPException(status_code=422, detail="Ano inválido.")
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    announcements = (
        db.query(CalendarAnnouncement)
        .filter(CalendarAnnouncement.event_date >= start, CalendarAnnouncement.event_date <= end)
        .order_by(CalendarAnnouncement.event_date.asc(), CalendarAnnouncement.id.asc())
        .all()
    )
    tournaments = filter_calendar_tournaments(
        svc.list_calendar_events(year, month),
        viewer,
        db,
    )
    cutoff = promo_public_cutoff()
    promos = (
        db.query(PromoAction)
        .filter(
            PromoAction.published.is_(True),
            PromoAction.show_in_calendar.is_(True),
            PromoAction.end_date >= cutoff,
            PromoAction.start_date <= end,
            PromoAction.end_date >= start,
        )
        .order_by(PromoAction.start_date.asc(), PromoAction.id.asc())
        .all()
    )
    return {
        "tournaments": tournaments,
        "announcements": [_announcement_dict(a) for a in announcements],
        "promo_actions": [_promo_calendar_dict(row) for row in promos],
    }


@router.get("/calendar/announcements")
def list_announcements(
    _: RequireStaff,
    db: Session = Depends(get_db),
    year: int | None = None,
    month: int | None = None,
):
    query = db.query(CalendarAnnouncement).order_by(
        CalendarAnnouncement.event_date.desc(),
        CalendarAnnouncement.id.desc(),
    )
    if year is not None and month is not None:
        if month < 1 or month > 12:
            raise HTTPException(status_code=422, detail="Mês inválido.")
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        query = query.filter(
            CalendarAnnouncement.event_date >= start,
            CalendarAnnouncement.event_date <= end,
        )
    rows = query.limit(200).all()
    return [_announcement_dict(a) for a in rows]


@router.post("/calendar/announcements", status_code=201)
def create_announcement(
    body: AnnouncementBody,
    actor: RequireStaff,
    db: Session = Depends(get_db),
):
    row = CalendarAnnouncement(
        title=body.title.strip(),
        event_date=body.event_date,
        description=(body.description or "").strip() or None,
        start_time=_validate_time(body.start_time),
        location=(body.location or "").strip() or None,
        created_by_user_id=actor.id,
    )
    if not row.title:
        raise HTTPException(status_code=422, detail="Título é obrigatório.")
    db.add(row)
    db.commit()
    db.refresh(row)
    return _announcement_dict(row)


@router.patch("/calendar/announcements/{announcement_id}")
def update_announcement(
    announcement_id: int,
    body: AnnouncementPatchBody,
    _: RequireStaff,
    db: Session = Depends(get_db),
):
    row = db.query(CalendarAnnouncement).filter(CalendarAnnouncement.id == announcement_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    data = body.model_dump(exclude_unset=True)
    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            raise HTTPException(status_code=422, detail="Título é obrigatório.")
        row.title = title
    if "event_date" in data and data["event_date"] is not None:
        row.event_date = data["event_date"]
    if "description" in data:
        row.description = (data["description"] or "").strip() or None
    if "start_time" in data:
        row.start_time = _validate_time(data["start_time"])
    if "location" in data:
        row.location = (data["location"] or "").strip() or None
    db.commit()
    db.refresh(row)
    return _announcement_dict(row)


@router.delete("/calendar/announcements/{announcement_id}", status_code=204)
def delete_announcement(
    announcement_id: int,
    _: RequireStaff,
    db: Session = Depends(get_db),
):
    row = db.query(CalendarAnnouncement).filter(CalendarAnnouncement.id == announcement_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    db.delete(row)
    db.commit()
