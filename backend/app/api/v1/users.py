"""Users admin/staff APIs + public profiles/ranking."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireStaff, get_optional_user
from app.core.auth import AuthError, create_incomplete_user, create_invite, private_user_dict, public_user_dict
from app.core.auth.fourse_points import ranking, user_fp_total
from app.db.session import get_db
from app.models import Event, Player, User, UserRole, UserStatus

router = APIRouter(tags=["users"])


class CreateUserBody(BaseModel):
    display_name: str
    email: str
    phone: str
    role: str = UserRole.player.value
    birth_date: date | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    guardian_relation: str | None = None


@router.get("/users")
def list_users(
    _: RequireAdmin,
    db: Session = Depends(get_db),
    q: str | None = None,
):
    query = db.query(User).order_by(User.display_name.asc())
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (User.display_name.ilike(like)) | (User.email.ilike(like)) | (User.phone.ilike(like))
        )
    return [private_user_dict(u) for u in query.all()]


@router.post("/users", status_code=201)
def create_user(
    body: CreateUserBody,
    actor: RequireStaff,
    db: Session = Depends(get_db),
):
    if body.role not in {UserRole.player.value, UserRole.staff.value, UserRole.admin.value}:
        raise HTTPException(status_code=400, detail="Papel inválido.")
    if actor.role != UserRole.admin.value and body.role != UserRole.player.value:
        raise HTTPException(status_code=403, detail="Staff só pode criar jogadores.")
    try:
        user = create_incomplete_user(
            db,
            display_name=body.display_name,
            email=body.email,
            phone=body.phone,
            role=body.role,
            birth_date=body.birth_date,
            guardian_name=body.guardian_name,
            guardian_phone=body.guardian_phone,
            guardian_relation=body.guardian_relation,
        )
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return private_user_dict(user)


@router.post("/users/{user_id}/invite")
def invite_user(user_id: int, _: RequireAdmin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    try:
        invite = create_invite(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "token": invite.token,
        "expires_at": invite.expires_at.isoformat(),
        "claim_path": f"/convite/{invite.token}",
        "user": private_user_dict(user),
    }


@router.get("/users/search")
def search_users(
    _: RequireStaff,
    db: Session = Depends(get_db),
    q: str = Query(min_length=1),
):
    like = f"%{q.strip()}%"
    rows = (
        db.query(User)
        .filter((User.display_name.ilike(like)) | (User.email.ilike(like)) | (User.phone.ilike(like)))
        .order_by(User.display_name.asc())
        .limit(30)
        .all()
    )
    return [public_user_dict(u) | {"email": u.email, "phone": u.phone, "status": u.status} for u in rows]


@router.get("/ranking")
def public_ranking(db: Session = Depends(get_db), limit: int = Query(default=50, ge=1, le=200)):
    return ranking(db, limit=limit)


@router.get("/jogadores/{user_id}/perfil")
def public_profile(user_id: int, db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user)):
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None or user.role == UserRole.admin.value:
        # Hide pure admin accounts from public directory unless they also play
        entries = db.query(Player).filter(Player.user_id == user_id).count()
        if user is None or (user.role == UserRole.admin.value and entries == 0):
            raise HTTPException(status_code=404, detail="Jogador não encontrado.")
    history = []
    players = db.query(Player).filter(Player.user_id == user_id).all()
    event_ids = [p.event_id for p in players]
    events = {e.id: e for e in db.query(Event).filter(Event.id.in_(event_ids)).all()} if event_ids else {}
    for p in players:
        ev = events.get(p.event_id)
        if not ev or ev.status != "finished":
            continue
        snap = (ev.premiacao_resultado or {}).get("standings_snapshot") or []
        row = next((s for s in snap if s.get("player_id") == p.id), None)
        history.append(
            {
                "event_id": ev.id,
                "event_name": ev.name,
                "event_date": ev.event_date.isoformat(),
                "source": ev.source,
                "rank": row.get("rank") if row else None,
                "rank_label": row.get("rank_label") if row else None,
                "is_drop": row.get("is_drop") if row else bool(p.dropped_at),
                "decklist": p.decklist,
            }
        )
    history.sort(key=lambda h: h["event_date"], reverse=True)
    return {
        **public_user_dict(user),
        "fourse_points": user_fp_total(db, user.id),
        "history": history,
        "viewer_authenticated": viewer is not None,
    }
