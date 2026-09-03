"""Users admin/staff APIs + public profiles/ranking."""

from __future__ import annotations

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireStaff, get_optional_user
from app.core.audit import log_staff_action
from app.core.auth import AuthError, create_incomplete_user, create_password_reset, is_email_verified, private_user_dict, public_user_dict
from app.core.auth.account_lifecycle import delete_user_account
from app.core.auth.invite_delivery import provision_invite_and_email
from app.core.auth.invites import invite_claim_path, invite_claim_url, password_reset_path, password_reset_url
from app.core.email.outbound import send_password_reset_email
from app.core.auth.fourse_points import ranking
from app.core.privacy import can_contact_for_marketing
from app.core.rate_limit import check_rate_limit_scope, rate_limit_dependency
from app.db.session import get_db
from app.models import User, UserRole, UserStatus
from app.core.search import ilike_contains
from app.services.profile_service import build_public_profile

_LIKE_ESCAPE = "\\"

router = APIRouter(tags=["users"])

_users_invite_limit = rate_limit_dependency("users_invite_resend", limit=30, window_sec=300)


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
    actor: RequireAdmin,
    request: Request,
    db: Session = Depends(get_db),
    q: str | None = None,
):
    query = db.query(User).filter(User.status != UserStatus.deleted.value).order_by(User.display_name.asc())
    if q:
        like = ilike_contains(q)
        query = query.filter(
            (User.display_name.ilike(like, escape=_LIKE_ESCAPE))
            | (User.email.ilike(like, escape=_LIKE_ESCAPE))
            | (User.phone.ilike(like, escape=_LIKE_ESCAPE))
        )
    rows = query.all()
    log_staff_action(
        db,
        actor=actor,
        action="user.list",
        meta={"count": len(rows), "q": (q or "")[:80] or None},
        request=request,
    )
    return [private_user_dict(u) for u in rows]


@router.get("/users/export-contacts")
def export_contacts(
    actor: RequireAdmin,
    request: Request,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(User)
        .filter(User.status == UserStatus.active.value)
        .order_by(User.display_name.asc())
        .all()
    )
    eligible = [u for u in rows if can_contact_for_marketing(u)]
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["nome", "telefone"])
    for u in eligible:
        writer.writerow([u.display_name, u.phone or ""])
    log_staff_action(
        db,
        actor=actor,
        action="marketing.export",
        meta={"count": len(eligible)},
        request=request,
    )
    data = buf.getvalue().encode("utf-8")
    filename = f"fourse-contatos-{date.today().isoformat()}.csv"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/users", status_code=201)
def create_user(
    body: CreateUserBody,
    actor: RequireStaff,
    request: Request,
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
    try:
        provision_invite_and_email(db, user)
    except Exception:
        pass
    log_staff_action(
        db,
        actor=actor,
        action="user.create_incomplete",
        target_user_id=user.id,
        meta={"role": user.role},
        request=request,
    )
    return private_user_dict(user)


@router.post("/users/{user_id}/invite")
def invite_user(
    user_id: int,
    actor: RequireAdmin,
    request: Request,
    db: Session = Depends(get_db),
    __: None = Depends(_users_invite_limit),
):
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None or user.status == UserStatus.deleted.value:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    check_rate_limit_scope("users_invite_user", str(user_id), limit=1, window_sec=300)
    try:
        raw, invite = provision_invite_and_email(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_staff_action(
        db,
        actor=actor,
        action="user.invite",
        target_user_id=user.id,
        request=request,
    )
    return {
        "expires_at": invite.expires_at.isoformat(),
        "claim_path": invite_claim_path(raw),
        "claim_url": invite_claim_url(raw),
        "user": private_user_dict(user),
        "email_sent": True,
    }


@router.post("/users/{user_id}/password-reset")
def reset_user_password(
    user_id: int,
    actor: RequireAdmin,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None or user.status == UserStatus.deleted.value:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if actor.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Use Alterar senha na própria conta. Reset por link é para outros usuários.",
        )
    try:
        raw_token, row = create_password_reset(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if is_email_verified(user):
        try:
            send_password_reset_email(user, raw_token)
        except Exception:
            pass
    log_staff_action(
        db,
        actor=actor,
        action="user.password_reset",
        target_user_id=user.id,
        request=request,
    )
    return {
        "expires_at": row.expires_at.isoformat(),
        "reset_path": password_reset_path(raw_token),
        "reset_url": password_reset_url(raw_token),
        "user": private_user_dict(user),
    }


@router.post("/users/{user_id}/delete")
def admin_delete_user(
    user_id: int,
    actor: RequireAdmin,
    request: Request,
    db: Session = Depends(get_db),
):
    if actor.id == user_id:
        raise HTTPException(status_code=400, detail="Use Excluir conta no próprio perfil.")
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if user.role == UserRole.admin.value:
        raise HTTPException(status_code=400, detail="Exclusão de administrador não permitida por esta via.")
    try:
        delete_user_account(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_staff_action(
        db,
        actor=actor,
        action="user.delete",
        target_user_id=user_id,
        request=request,
    )
    return {"ok": True}


@router.get("/users/search")
def search_users(
    actor: RequireStaff,
    request: Request,
    db: Session = Depends(get_db),
    q: str = Query(min_length=1),
):
    like = ilike_contains(q)
    rows = (
        db.query(User)
        .filter(
            User.status != UserStatus.deleted.value,
            (User.display_name.ilike(like, escape=_LIKE_ESCAPE))
            | (User.email.ilike(like, escape=_LIKE_ESCAPE))
            | (User.phone.ilike(like, escape=_LIKE_ESCAPE)),
        )
        .order_by(User.display_name.asc())
        .limit(30)
        .all()
    )
    log_staff_action(
        db,
        actor=actor,
        action="user.search",
        meta={"q": q[:80], "count": len(rows)},
        request=request,
    )
    return [public_user_dict(u) | {"email": u.email, "phone": u.phone, "status": u.status} for u in rows]


@router.get("/jogadores/buscar")
def public_player_search(
    db: Session = Depends(get_db),
    q: str = Query(min_length=2, max_length=80),
    limit: int = Query(default=12, ge=1, le=30),
):
    """Public search by display name only (no email/phone). Includes incomplete accounts."""
    like = ilike_contains(q)
    rows = (
        db.query(User)
        .filter(
            User.display_name.ilike(like, escape=_LIKE_ESCAPE),
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
    if user.status == UserStatus.deleted.value:
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")
    if user.status not in (UserStatus.active.value, UserStatus.incomplete.value):
        is_owner = bool(viewer and viewer.id == user.id)
        is_admin = bool(viewer and viewer.role == UserRole.admin.value)
        if not (is_owner or is_admin):
            raise HTTPException(status_code=404, detail="Jogador não encontrado.")
    return build_public_profile(db, user, viewer)


class UpdateUserRoleBody(BaseModel):
    role: str = Field(description="staff or player")


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    body: UpdateUserRoleBody,
    actor: RequireAdmin,
    request: Request,
    db: Session = Depends(get_db),
):
    if body.role not in {UserRole.staff.value, UserRole.player.value}:
        raise HTTPException(status_code=400, detail="Papel inválido. Use staff ou player.")
    if actor.id == user_id:
        raise HTTPException(status_code=403, detail="Não é possível alterar o próprio papel.")
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None or user.status == UserStatus.deleted.value:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if user.role == UserRole.admin.value:
        raise HTTPException(status_code=400, detail="Papel de administrador não pode ser alterado aqui.")
    if user.role == body.role:
        return private_user_dict(user)
    old = user.role
    user.role = body.role
    db.commit()
    db.refresh(user)
    log_staff_action(
        db,
        actor=actor,
        action="user.role_change",
        target_user_id=user.id,
        meta={"from": old, "to": body.role},
        request=request,
    )
    return private_user_dict(user)
