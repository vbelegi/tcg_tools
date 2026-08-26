"""Auth HTTP routes."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.auth import (
    ADMIN_EMAIL,
    AuthError,
    SESSION_COOKIE,
    SESSION_DAYS,
    authenticate,
    change_password,
    claim_invite,
    create_session,
    get_admin,
    private_user_dict,
    register_player,
    revoke_session,
)
from app.core.auth.passwords import MIN_PASSWORD_LEN
from app.db.session import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    email: str
    password: str
    # Back-compat for older clients
    username: str | None = None


class RegisterBody(BaseModel):
    display_name: str
    email: str
    phone: str
    password: str
    birth_date: date | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    guardian_relation: str | None = None


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


class ClaimInviteBody(BaseModel):
    token: str
    password: str
    birth_date: date | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    guardian_relation: str | None = None


@router.get("/status")
def auth_status(db: Session = Depends(get_db)):
    admin = get_admin(db)
    return {
        "configured": admin is not None,
        "min_password_length": MIN_PASSWORD_LEN,
    }


@router.get("/me")
def auth_me(user: User = Depends(get_current_user)):
    return private_user_dict(user)


@router.post("/login")
def login(body: LoginBody, response: Response, db: Session = Depends(get_db)):
    email = body.email or body.username or ""
    try:
        user = authenticate(db, email, body.password)
        token = create_session(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )
    return private_user_dict(user)


@router.post("/register", status_code=201)
def register(body: RegisterBody, response: Response, db: Session = Depends(get_db)):
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
        )
        token = create_session(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )
    return private_user_dict(user)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    revoke_session(db, token)
    response.delete_cookie(SESSION_COOKIE, path="/")
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
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True, "message": "Senha alterada. Faça login novamente."}


@router.post("/claim-invite")
def auth_claim_invite(body: ClaimInviteBody, response: Response, db: Session = Depends(get_db)):
    try:
        user = claim_invite(
            db,
            body.token,
            body.password,
            birth_date=body.birth_date,
            guardian_name=body.guardian_name,
            guardian_phone=body.guardian_phone,
            guardian_relation=body.guardian_relation,
        )
        token = create_session(db, user)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )
    return private_user_dict(user)
