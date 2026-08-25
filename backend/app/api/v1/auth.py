"""Auth HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.core.auth import (
    ADMIN_USERNAME,
    AuthError,
    SESSION_COOKIE,
    SESSION_DAYS,
    authenticate,
    change_password,
    create_session,
    get_admin,
    revoke_session,
)
from app.core.auth.passwords import MIN_PASSWORD_LEN
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(default=ADMIN_USERNAME)
    password: str


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


@router.get("/status")
def auth_status(db: Session = Depends(get_db)):
    admin = get_admin(db)
    return {
        "configured": admin is not None,
        "username": ADMIN_USERNAME,
        "min_password_length": MIN_PASSWORD_LEN,
    }


@router.get("/me")
def auth_me(user: User = Depends(get_current_user)):
    return {"username": user.username}


@router.post("/login")
def login(body: LoginBody, response: Response, db: Session = Depends(get_db)):
    try:
        user = authenticate(db, body.username, body.password)
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
    return {"username": user.username}


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
