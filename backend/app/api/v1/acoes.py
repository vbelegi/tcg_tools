"""Promotional actions API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Cookie, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import RequireStaff, get_optional_user
from app.api.uploads import read_upload_limited
from app.api.v1.event_visibility import is_staff_user
from app.api.v1.promo_visibility import can_view_promo, visible_promo_query
from app.core.audit import log_staff_action
from app.core.auth.cookies import clear_promo_enroll_cookie, set_promo_enroll_cookie
from app.core.auth.invites import promo_enroll_path, promo_enroll_url
from app.core.promo import regulations
from app.core.promo.enrollment import (
    ENROLL_COOKIE,
    ENROLL_TTL,
    EnrollmentError,
    complete_enrollment,
    consume_token,
    create_enrollment_token,
    get_participation,
)
from app.core.promo.regulations import (
    MAX_REGULATION_BYTES,
    RegulationError,
    store_regulation,
)
from app.core.promo.types import get_handler, is_known_type, known_types
from app.core.rate_limit import rate_limit_dependency
from app.db.session import get_db
from app.models import PromoAction, PromoParticipant, User

router = APIRouter(prefix="/acoes", tags=["acoes"])
_enroll_limit = rate_limit_dependency("promo_enroll", limit=30, window_sec=60)


class PromoActionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str
    start_date: date
    end_date: date
    description: str | None = None
    published: bool = False
    show_in_calendar: bool = True
    max_participants: int | None = Field(default=None, ge=1)


class PromoActionPatch(BaseModel):
    """`published` is absent on purpose: publishing goes through its own endpoint."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    show_in_calendar: bool | None = None
    max_participants: int | None = Field(default=None, ge=1)


def _current_regulation(action: PromoAction) -> dict | None:
    if not action.regulation_version:
        return None
    return {
        "version": action.regulation_version,
        "display_name": regulations.display_name(action, action.regulation_version),
        "url": f"/api/v1/media/acoes/{action.id}/regulamento",
    }


def _regulation_history(db: Session, action: PromoAction) -> list[dict]:
    return [
        {
            "version": row.version,
            "display_name": regulations.display_name(action, row.version),
            "url": f"/api/v1/media/acoes/{action.id}/regulamento/{row.version}",
            "uploaded_at": row.uploaded_at.isoformat() if row.uploaded_at else None,
            "uploaded_by_user_id": row.uploaded_by_user_id,
        }
        for row in regulations.list_versions(db, action.id)
    ]


def _participant_counts(db: Session, action_ids: list[int]) -> dict[int, int]:
    """One grouped query instead of a count per card."""
    if not action_ids:
        return {}
    rows = (
        db.query(PromoParticipant.promo_id, func.count(PromoParticipant.id))
        .filter(PromoParticipant.promo_id.in_(action_ids))
        .group_by(PromoParticipant.promo_id)
        .all()
    )
    return {int(promo_id): int(total) for promo_id, total in rows}


def _action_dict(
    db: Session,
    action: PromoAction,
    viewer: User | None,
    *,
    detail: bool = False,
    participant_count: int | None = None,
) -> dict:
    handler = get_handler(action.type)
    data: dict[str, Any] = {
        "id": action.id,
        "name": action.name,
        "type": action.type,
        "type_label": handler.label if handler else action.type,
        "start_date": action.start_date.isoformat(),
        "end_date": action.end_date.isoformat(),
        "description": action.description,
        "published": bool(action.published),
        "show_in_calendar": bool(action.show_in_calendar),
        "max_participants": action.max_participants,
        "regulation": _current_regulation(action),
        "created_at": action.created_at.isoformat() if action.created_at else None,
    }
    if detail:
        data["how_to_participate"] = handler.how_to_participate_text() if handler else None
        data["management_panel_key"] = handler.management_panel_key if handler else None
        if viewer is not None:
            mine = get_participation(db, action.id, viewer.id)
            data["my_participation"] = {"status": mine.status} if mine else None
    if is_staff_user(viewer):
        # Participant numbers are staff-only; players never see who or how many.
        data["participant_count"] = (
            participant_count
            if participant_count is not None
            else db.query(PromoParticipant)
            .filter(PromoParticipant.promo_id == action.id)
            .count()
        )
        if detail:
            data["regulation_versions"] = _regulation_history(db, action)
    return data


def _snapshot(action: PromoAction) -> dict:
    return {
        "name": action.name,
        "start_date": action.start_date.isoformat(),
        "end_date": action.end_date.isoformat(),
        "description": action.description,
        "show_in_calendar": bool(action.show_in_calendar),
        "max_participants": action.max_participants,
    }


def _diff(before: dict, after: dict) -> dict:
    return {
        key: {"from": value, "to": after.get(key)}
        for key, value in before.items()
        if value != after.get(key)
    }


def _validate_period(start: date, end: date) -> None:
    if end < start:
        raise HTTPException(
            status_code=400, detail="A data de término não pode ser anterior à data de início."
        )


def _get_action(db: Session, action_id: int) -> PromoAction:
    action = db.query(PromoAction).filter(PromoAction.id == action_id).one_or_none()
    if action is None:
        raise HTTPException(status_code=404, detail="Ação não encontrada.")
    return action


@router.get("/tipos")
def list_action_types(_: RequireStaff):
    return [{"key": handler.key, "label": handler.label} for handler in known_types()]


@router.get("")
def list_actions(
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
    q: str | None = None,
    active: bool | None = None,
    limit: int = Query(default=100, ge=1, le=200),
):
    # Filters go on top of the visibility rule, never before it, so a search
    # term can never surface an unpublished action.
    query = visible_promo_query(db, viewer)
    term = (q or "").strip()
    if term:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.filter(PromoAction.name.ilike(f"%{escaped}%", escape="\\"))
    if active:
        query = query.filter(PromoAction.end_date >= date.today())
    rows = (
        query.order_by(PromoAction.end_date.desc(), PromoAction.id.desc()).limit(limit).all()
    )
    counts = (
        _participant_counts(db, [row.id for row in rows]) if is_staff_user(viewer) else {}
    )
    return [
        _action_dict(db, row, viewer, participant_count=counts.get(row.id, 0)) for row in rows
    ]


@router.post("", status_code=201)
def create_action(
    body: PromoActionCreate,
    actor: RequireStaff,
    request: Request,
    db: Session = Depends(get_db),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nome é obrigatório.")
    if not is_known_type(body.type):
        raise HTTPException(status_code=400, detail="Tipo de ação inválido.")
    _validate_period(body.start_date, body.end_date)

    action = PromoAction(
        name=name,
        type=body.type,
        start_date=body.start_date,
        end_date=body.end_date,
        description=(body.description or "").strip() or None,
        published=bool(body.published),
        show_in_calendar=bool(body.show_in_calendar),
        max_participants=body.max_participants,
        created_by_user_id=actor.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    log_staff_action(
        db,
        actor=actor,
        action="promo.create",
        meta={
            "promo_id": action.id,
            "name": action.name,
            "type": action.type,
            "published": bool(action.published),
        },
        request=request,
    )
    return _action_dict(db, action, actor, detail=True)


@router.get("/{action_id}")
def get_action(
    action_id: int,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    action = _get_action(db, action_id)
    if not can_view_promo(action, viewer):
        # 404 rather than 403 so a draft's existence is not leaked.
        raise HTTPException(status_code=404, detail="Ação não encontrada.")
    return _action_dict(db, action, viewer, detail=True)


@router.patch("/{action_id}")
def update_action(
    action_id: int,
    body: PromoActionPatch,
    actor: RequireStaff,
    request: Request,
    db: Session = Depends(get_db),
):
    action = _get_action(db, action_id)
    data = body.model_dump(exclude_unset=True)

    if "type" in data and data["type"] is not None and data["type"] != action.type:
        raise HTTPException(
            status_code=400,
            detail="O tipo da ação não pode ser alterado após a criação.",
        )

    before = _snapshot(action)
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Nome é obrigatório.")
        action.name = name
    if "start_date" in data and data["start_date"] is not None:
        action.start_date = data["start_date"]
    if "end_date" in data and data["end_date"] is not None:
        action.end_date = data["end_date"]
    if "description" in data:
        action.description = (data["description"] or "").strip() or None
    if "show_in_calendar" in data and data["show_in_calendar"] is not None:
        action.show_in_calendar = bool(data["show_in_calendar"])
    if "max_participants" in data:
        action.max_participants = data["max_participants"]

    _validate_period(action.start_date, action.end_date)
    db.commit()
    db.refresh(action)

    changes = _diff(before, _snapshot(action))
    if changes:
        log_staff_action(
            db,
            actor=actor,
            action="promo.edit",
            meta={"promo_id": action.id, "changes": changes},
            request=request,
        )
    return _action_dict(db, action, actor, detail=True)


@router.post("/{action_id}/publish")
def publish_action(
    action_id: int,
    actor: RequireStaff,
    request: Request,
    db: Session = Depends(get_db),
):
    action = _get_action(db, action_id)
    if action.published:
        # Idempotent: a double click must not re-audit or re-notify.
        return _action_dict(db, action, actor, detail=True)
    action.published = True
    db.commit()
    db.refresh(action)
    log_staff_action(
        db,
        actor=actor,
        action="promo.publish",
        meta={"promo_id": action.id},
        request=request,
    )
    return _action_dict(db, action, actor, detail=True)


@router.post("/{action_id}/regulamento")
async def upload_regulation(
    action_id: int,
    actor: RequireStaff,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    action = _get_action(db, action_id)
    previous = action.regulation_version
    data = await read_upload_limited(file, MAX_REGULATION_BYTES)
    try:
        row = store_regulation(db, action, data, file.content_type, uploaded_by=actor)
    except RegulationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_staff_action(
        db,
        actor=actor,
        action="promo.regulation",
        meta={"promo_id": action.id, "from": previous, "to": row.version},
        request=request,
    )
    return _action_dict(db, action, actor, detail=True)


def _enroll_response(result) -> JSONResponse:
    response = JSONResponse(status_code=result.http_status, content=result.as_dict())
    if result.set_cookie:
        set_promo_enroll_cookie(
            response,
            result.set_cookie,
            max_age=result.cookie_max_age or int(ENROLL_TTL.total_seconds()),
        )
    if result.clear_cookie:
        clear_promo_enroll_cookie(response)
    return response


@router.post("/{action_id}/enrollment-token")
def create_action_enrollment_token(
    action_id: int,
    actor: RequireStaff,
    request: Request,
    db: Session = Depends(get_db),
):
    action = _get_action(db, action_id)
    try:
        raw, row = create_enrollment_token(db, action, actor)
    except EnrollmentError as exc:
        from app.core.promo.enrollment import HTTP_STATUS

        raise HTTPException(
            status_code=HTTP_STATUS[exc.reason],
            detail={"reason": exc.reason, "message": str(exc)},
        ) from exc
    log_staff_action(
        db,
        actor=actor,
        action="promo.enroll_token",
        meta={"promo_id": action.id},
        request=request,
    )
    return {
        "path": promo_enroll_path(raw),
        "url": promo_enroll_url(raw),
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "expires_in_seconds": int(ENROLL_TTL.total_seconds()),
    }


@router.get("/enroll/{raw_token}")
def consume_enrollment_token(
    raw_token: str,
    request: Request,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
    promo_enroll: str | None = Cookie(default=None, alias=ENROLL_COOKIE),
    _: None = Depends(_enroll_limit),
):
    result = consume_token(db, raw_token, viewer, promo_enroll)
    return _enroll_response(result)


@router.post("/enroll/complete")
def complete_enrollment_endpoint(
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
    promo_enroll: str | None = Cookie(default=None, alias=ENROLL_COOKIE),
    _: None = Depends(_enroll_limit),
):
    result = complete_enrollment(db, viewer, promo_enroll)
    return _enroll_response(result)
