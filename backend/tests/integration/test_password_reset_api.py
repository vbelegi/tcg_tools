"""Admin-initiated password reset."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import register_player, create_password_reset
from app.core.auth.session_tokens import hash_session_token
from app.models import PasswordResetToken, User
from datetime import date


def test_admin_password_reset_flow(api_client: TestClient, db_session: Session):
    player = register_player(
        db_session,
        display_name="Reset Me",
        email="reset.me@example.com",
        phone="+5511999887766",
        password="oldpassword1",
        birth_date=date(1990, 1, 1),
    )

    r = api_client.post(f"/api/v1/users/{player.id}/password-reset")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reset_path"].startswith("/redefinir-senha/")
    token = body["reset_path"].rsplit("/", 1)[-1]

    row = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == player.id).one()
    assert row.token == hash_session_token(token)

    api_client.post("/api/v1/auth/logout")
    claim = api_client.post(
        "/api/v1/auth/claim-password-reset",
        json={"token": token, "password": "newpassword1"},
    )
    assert claim.status_code == 200, claim.text
    assert api_client.get("/api/v1/auth/me").status_code == 200

    api_client.post("/api/v1/auth/logout")
    bad = api_client.post(
        "/api/v1/auth/login",
        json={"email": "reset.me@example.com", "password": "oldpassword1"},
    )
    assert bad.status_code == 401
    good = api_client.post(
        "/api/v1/auth/login",
        json={"email": "reset.me@example.com", "password": "newpassword1"},
    )
    assert good.status_code == 200


def test_password_reset_rejects_short_password(api_client: TestClient, db_session: Session):
    player = register_player(
        db_session,
        display_name="Short Reset",
        email="short.reset@example.com",
        phone="+5511999887700",
        password="oldpassword1",
        birth_date=date(1990, 1, 1),
    )
    raw, _ = create_password_reset(db_session, player)
    api_client.post("/api/v1/auth/logout")
    r = api_client.post(
        "/api/v1/auth/claim-password-reset",
        json={"token": raw, "password": "short"},
    )
    assert r.status_code == 400


def test_cannot_reset_own_password_via_admin_endpoint(api_client: TestClient, db_session: Session):
    admin = db_session.query(User).filter(User.email == "admin@local").one()
    r = api_client.post(f"/api/v1/users/{admin.id}/password-reset")
    assert r.status_code == 400
