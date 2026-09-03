"""Auth HTTP routes."""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.uploads import read_upload_limited
from app.core.auth import (
    AuthError,
    authenticate,
    change_password,
    claim_invite,
    claim_password_reset,
    create_email_verification,
    create_password_reset,
    create_session,
    get_admin,
    get_user_by_email,
    is_email_verified,
    private_user_dict,
    register_player,
    revoke_session,
    verify_email,
)
from app.core.auth.account_lifecycle import delete_user_account
from app.core.auth.cookies import clear_session_cookie, set_session_cookie
from app.core.auth.passwords import MIN_PASSWORD_LEN, normalize_email
from app.core.auth.service import SESSION_COOKIE, ensure_unique_email_phone, require_guardian_if_minor
from app.core.auth.avatars import AvatarError, encode_user_avatar, MAX_UPLOAD_BYTES
from app.core.email.outbound import (
    forgot_password_generic_message,
    send_password_reset_email,
    send_verification_email,
)
from app.core.privacy import PRIVACY_POLICY_VERSION, TERMS_VERSION
from app.core.rate_limit import check_rate_limit_scope, rate_limit_dependency
from app.db.session import get_db
from app.models import Event, FoursePointsLedger, Player, User, UserRole, UserStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_auth_login_limit = rate_limit_dependency("auth_login", limit=10, window_sec=60)
_auth_register_limit = rate_limit_dependency("auth_register", limit=5, window_sec=300)
_auth_claim_limit = rate_limit_dependency("auth_claim_invite", limit=10, window_sec=300)
_auth_reset_claim_limit = rate_limit_dependency("auth_claim_password_reset", limit=10, window_sec=300)
_auth_resend_verify_ip_limit = rate_limit_dependency("auth_resend_verification_ip", limit=3, window_sec=3600)
_auth_forgot_limit = rate_limit_dependency("auth_forgot_password", limit=10, window_sec=60)


class LoginBody(BaseModel):
    email: str
    password: str
    username: str | None = None


class RegisterBody(BaseModel):
    display_name: str
    email: str
    phone: str
    password: str
    birth_date: date
    guardian_name: str | None = None
    guardian_phone: str | None = None
    guardian_relation: str | None = None
    accept_privacy: bool = False


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


class ClaimInviteBody(BaseModel):
    token: str
    password: str
    birth_date: date
    guardian_name: str | None = None
    guardian_phone: str | None = None
    guardian_relation: str | None = None
    accept_privacy: bool = False


class ClaimPasswordResetBody(BaseModel):
    token: str
    password: str


class VerifyEmailBody(BaseModel):
    token: str


class ForgotPasswordBody(BaseModel):
    email: str


class UpdateMeBody(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = None
    birth_date: date | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    guardian_relation: str | None = None
    marketing_opt_out: bool | None = None


class DeleteMeBody(BaseModel):
    password: str
    confirm: str = Field(description='Must be "EXCLUIR"')


@router.get("/status")
def auth_status(db: Session = Depends(get_db)):
    admin = get_admin(db)
    return {
        "configured": admin is not None,
        "min_password_length": MIN_PASSWORD_LEN,
        "privacy_policy_version": PRIVACY_POLICY_VERSION,
        "terms_version": TERMS_VERSION,
    }


@router.get("/me")
def auth_me(user: User = Depends(get_current_user)):
    return private_user_dict(user)


@router.patch("/me")
def auth_update_me(
    body: UpdateMeBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.status == UserStatus.deleted.value:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    try:
        if body.display_name is not None:
            name = body.display_name.strip()
            if not name:
                raise HTTPException(status_code=400, detail="Nome inválido.")
            user.display_name = name
        if body.phone is not None:
            _, phone_n = ensure_unique_email_phone(
                db, email=user.email, phone=body.phone, exclude_user_id=user.id
            )
            user.phone = phone_n
        if body.birth_date is not None:
            user.birth_date = body.birth_date
        if body.guardian_name is not None:
            user.guardian_name = body.guardian_name.strip() or None
        if body.guardian_phone is not None:
            user.guardian_phone = body.guardian_phone.strip() or None
        if body.guardian_relation is not None:
            user.guardian_relation = body.guardian_relation.strip() or None
        if any(
            x is not None
            for x in (body.birth_date, body.guardian_name, body.guardian_phone, body.guardian_relation)
        ):
            require_guardian_if_minor(user.birth_date, user.guardian_name, user.guardian_phone)
        if body.marketing_opt_out is not None:
            user.marketing_opt_out = bool(body.marketing_opt_out)
            if user.marketing_opt_out:
                from datetime import datetime

                user.marketing_opt_out_at = datetime.utcnow()
                user.marketing_opt_out_source = "profile"
            else:
                user.marketing_opt_out_at = None
                user.marketing_opt_out_source = None
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.add(user)
    db.commit()
    db.refresh(user)
    return private_user_dict(user)


@router.get("/me/export")
def auth_export_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.status == UserStatus.deleted.value:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    players = db.query(Player).filter(Player.user_id == user.id).all()
    event_ids = {p.event_id for p in players}
    events = (
        db.query(Event).filter(Event.id.in_(event_ids)).all() if event_ids else []
    )
    events_by_id = {e.id: e for e in events}
    fp_rows = db.query(FoursePointsLedger).filter(FoursePointsLedger.user_id == user.id).all()
    return {
        "exported_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "user": private_user_dict(user),
        "registrations": [
            {
                "event_id": p.event_id,
                "event_name": events_by_id[p.event_id].name if p.event_id in events_by_id else None,
                "event_date": (
                    events_by_id[p.event_id].event_date.isoformat()
                    if p.event_id in events_by_id
                    else None
                ),
                "player_name": p.name,
                "decklist": p.decklist,
                "attendance": p.attendance,
                "dropped_at": p.dropped_at.isoformat() if p.dropped_at else None,
            }
            for p in players
        ],
        "fourse_points": [
            {
                "event_id": r.event_id,
                "placement": r.placement,
                "points": r.points,
                "reason": r.reason,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in fp_rows
        ],
    }


@router.post("/me/delete")
def auth_delete_me(
    body: DeleteMeBody,
    response: Response,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.confirm.strip().upper() != "EXCLUIR":
        raise HTTPException(status_code=400, detail='Confirme digitando EXCLUIR.')
    from app.core.auth.passwords import verify_password

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Senha incorreta.")
    if user.role == UserRole.admin.value:
        admins = (
            db.query(User)
            .filter(User.role == UserRole.admin.value, User.status == UserStatus.active.value)
            .count()
        )
        if admins <= 1:
            raise HTTPException(status_code=400, detail="Não é possível excluir o único administrador.")
    try:
        delete_user_account(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    clear_session_cookie(response)
    return {"ok": True}


@router.post("/me/avatar")
async def auth_upload_avatar(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
):
    data = await read_upload_limited(file, MAX_UPLOAD_BYTES)
    try:
        blob = encode_user_avatar(data, file.content_type)
    except AvatarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    user.avatar_blob = blob
    db.add(user)
    db.commit()
    db.refresh(user)
    return private_user_dict(user)


@router.post("/login")
def login(
    body: LoginBody,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(_auth_login_limit),
):
    email = body.email or body.username or ""
    try:
        user = authenticate(db, email, body.password)
        token = create_session(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    set_session_cookie(response, token)
    return private_user_dict(user)


@router.post("/register", status_code=201)
def register(
    body: RegisterBody,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(_auth_register_limit),
):
    try:
        user = register_player(
            db,
            display_name=body.display_name,
            email=body.email,
            phone=body.phone,
            password=body.password,
            birth_date=body.birth_date,
            guardian_name=body.guardian_name,
            guardian_phone=body.guardian_phone,
            guardian_relation=body.guardian_relation,
            accept_privacy=body.accept_privacy,
        )
        token = create_session(db, user)
        raw_verify, _ = create_email_verification(db, user)
        try:
            send_verification_email(user, raw_verify)
        except Exception:
            logger.exception("Failed to send verification email on register user_id=%s", user.id)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    set_session_cookie(response, token)
    return private_user_dict(user)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    revoke_session(db, token)
    clear_session_cookie(response)
    return {"ok": True}


@router.post("/change-password")
def auth_change_password(
    body: ChangePasswordBody,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        change_password(db, user, body.current_password, body.new_password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    clear_session_cookie(response)
    return {"ok": True, "message": "Senha alterada. Faça login novamente."}


@router.post("/claim-invite")
def auth_claim_invite(
    body: ClaimInviteBody,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(_auth_claim_limit),
):
    try:
        user = claim_invite(
            db,
            body.token,
            body.password,
            birth_date=body.birth_date,
            guardian_name=body.guardian_name,
            guardian_phone=body.guardian_phone,
            guardian_relation=body.guardian_relation,
            accept_privacy=body.accept_privacy,
        )
        token = create_session(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    set_session_cookie(response, token)
    return private_user_dict(user)


@router.post("/claim-password-reset")
def auth_claim_password_reset(
    body: ClaimPasswordResetBody,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(_auth_reset_claim_limit),
):
    try:
        user = claim_password_reset(db, body.token, body.password)
        token = create_session(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    set_session_cookie(response, token)
    return private_user_dict(user)


@router.post("/verify-email")
def auth_verify_email(body: VerifyEmailBody, db: Session = Depends(get_db)):
    try:
        user = verify_email(db, body.token)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    from app.core.promo.enrollment import promote_pending_on_verify

    promote_pending_on_verify(db, user)
    return private_user_dict(user)


@router.post("/resend-verification")
def auth_resend_verification(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(_auth_resend_verify_ip_limit),
):
    if is_email_verified(user):
        raise HTTPException(status_code=400, detail="E-mail já verificado.")
    check_rate_limit_scope(
        "auth_resend_verification_user",
        str(user.id),
        limit=1,
        window_sec=600,
    )
    try:
        raw, _ = create_email_verification(db, user)
        send_verification_email(user, raw)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Failed to resend verification email user_id=%s", user.id)
        raise HTTPException(status_code=500, detail="Não foi possível enviar o e-mail. Tente mais tarde.") from None
    return {"ok": True, "message": "E-mail de verificação enviado."}


@router.post("/forgot-password")
def auth_forgot_password(
    body: ForgotPasswordBody,
    db: Session = Depends(get_db),
    _: None = Depends(_auth_forgot_limit),
):
    msg = forgot_password_generic_message()
    try:
        email_n = normalize_email(body.email)
    except AuthError:
        return {"ok": True, "message": msg}
    check_rate_limit_scope("auth_forgot_password_email", email_n, limit=1, window_sec=1800)
    user = get_user_by_email(db, email_n)
    if user and is_email_verified(user):
        try:
            raw, _ = create_password_reset(db, user)
            send_password_reset_email(user, raw)
        except Exception:
            logger.exception("Failed to send forgot-password email for user_id=%s", user.id)
    return {"ok": True, "message": msg}
