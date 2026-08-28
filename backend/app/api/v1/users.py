"""Users admin/staff APIs + public profiles/ranking."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireStaff, get_optional_user
from app.core.auth import AuthError, create_incomplete_user, create_invite, private_user_dict, public_user_dict
from app.core.auth.invites import invite_claim_path, invite_claim_url
from app.core.auth.fourse_points import ranking
from app.db.session import get_db
from app.models import User, UserRole, UserStatus
from app.services.profile_service import build_public_profile

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
        "claim_path": invite_claim_path(invite.token),
        "claim_url": invite_claim_url(invite.token),
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


@router.get("/jogadores/buscar")
def public_player_search(
    db: Session = Depends(get_db),
    q: str = Query(min_length=2, max_length=80),
    limit: int = Query(default=12, ge=1, le=30),
):
    """Public search by display name only (no email/phone). Includes incomplete accounts."""
    like = f"%{q.strip()}%"
    rows = (
        db.query(User)
        .filter(
            User.display_name.ilike(like),
            User.status.in_([UserStatus.active.value, UserStatus.incomplete.value]),
        )
        .order_by(User.display_name.asc())
        .limit(limit * 2)
        .all()
    )
    out = []
    for u in rows:
        out.append(
            {
                "id": u.id,
                "display_name": u.display_name,
                "avatar_url": public_user_dict(u).get("avatar_url"),
            }
        )
        if len(out) >= limit:
            break
    return out


@router.get("/ranking")
def public_ranking(db: Session = Depends(get_db), limit: int = Query(default=50, ge=1, le=200)):
    return ranking(db, limit=limit)


@router.get("/jogadores/{user_id}/perfil")
def public_profile(user_id: int, db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user)):
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")
    # Incomplete accounts are public (decklists/histórico); other non-active stay private.
    if user.status not in (UserStatus.active.value, UserStatus.incomplete.value):
        is_owner = bool(viewer and viewer.id == user.id)
        is_admin = bool(viewer and viewer.role == UserRole.admin.value)
        if not (is_owner or is_admin):
            raise HTTPException(status_code=404, detail="Jogador não encontrado.")
    return build_public_profile(db, user, viewer)
