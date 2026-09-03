"""Email change (two-step) and phone fields on profile update."""

from __future__ import annotations

from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import register_player, request_email_change
from app.core.auth.session_tokens import generate_session_token, hash_session_token
from app.core.rate_limit import reset_rate_limits_for_tests
from app.models import EmailChangeToken, EmailVerificationToken, Session as AuthSession, StaffAuditLog


def _login(client: TestClient, email: str, password: str = "password1234") -> None:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text


def test_verified_email_change_pending_then_confirm(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    user = register_player(
        db_session,
        display_name="Change Me",
        email="old.change@example.com",
        phone="+5511999887710",
        password="password1234",
        birth_date=date(1995, 1, 1),
    )
    user.email_verified_at = datetime.utcnow()
    db_session.commit()
    _login(api_client, user.email)

    from datetime import timedelta

    other_raw = generate_session_token()
    db_session.add(
        AuthSession(
            token=hash_session_token(other_raw),
            user_id=user.id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
    )
    db_session.commit()
    assert db_session.query(AuthSession).filter_by(user_id=user.id).count() >= 2

    r = api_client.post(
        "/api/v1/auth/me/email-change",
        json={"current_password": "password1234", "new_email": "new.change@example.com"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pending"] is True
    assert body["user"]["email"] == "old.change@example.com"
    assert body["user"]["pending_email"] == "new.change@example.com"

    me = api_client.get("/api/v1/auth/me")
    assert me.json()["pending_email"] == "new.change@example.com"

    # Replace token with a known raw value via service (API does not return raw)
    db_session.query(EmailChangeToken).filter(EmailChangeToken.user_id == user.id).delete()
    db_session.commit()
    raw, token_row, pending = request_email_change(
        db_session,
        user,
        current_password="password1234",
        new_email="new.change@example.com",
    )
    assert pending and raw and token_row

    confirm = api_client.post("/api/v1/auth/email-change/confirm", json={"token": raw})
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["email"] == "new.change@example.com"
    assert confirm.json()["email_verified"] is True
    assert confirm.json()["pending_email"] is None

    db_session.refresh(user)
    assert user.email == "new.change@example.com"
    remaining = db_session.query(AuthSession).filter_by(user_id=user.id).all()
    assert all(s.token != hash_session_token(other_raw) for s in remaining)

    audits = (
        db_session.query(StaffAuditLog)
        .filter(StaffAuditLog.action == "account.email_change", StaffAuditLog.target_user_id == user.id)
        .all()
    )
    assert any(a.meta and a.meta.get("status") == "confirmed" for a in audits)


def test_unverified_email_change_is_direct(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    user = register_player(
        db_session,
        display_name="Unverified",
        email="unverified.old@example.com",
        phone="+5511999887711",
        password="password1234",
        birth_date=date(1995, 1, 1),
    )
    assert user.email_verified_at is None
    _login(api_client, user.email)

    r = api_client.post(
        "/api/v1/auth/me/email-change",
        json={"current_password": "password1234", "new_email": "unverified.new@example.com"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["pending"] is False
    assert r.json()["user"]["email"] == "unverified.new@example.com"
    assert r.json()["user"]["email_verified"] is False

    db_session.refresh(user)
    assert user.email == "unverified.new@example.com"
    assert (
        db_session.query(EmailVerificationToken)
        .filter(EmailVerificationToken.user_id == user.id, EmailVerificationToken.used_at.is_(None))
        .count()
        == 1
    )
    assert db_session.query(EmailChangeToken).filter_by(user_id=user.id).count() == 0


def test_email_change_cancel_authenticated(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    user = register_player(
        db_session,
        display_name="Cancel Auth",
        email="cancel.auth@example.com",
        phone="+5511999887712",
        password="password1234",
        birth_date=date(1995, 1, 1),
    )
    user.email_verified_at = datetime.utcnow()
    db_session.commit()
    _login(api_client, user.email)

    api_client.post(
        "/api/v1/auth/me/email-change",
        json={"current_password": "password1234", "new_email": "cancel.auth.new@example.com"},
    )
    assert api_client.get("/api/v1/auth/me").json()["pending_email"] == "cancel.auth.new@example.com"

    cancelled = api_client.post("/api/v1/auth/me/email-change/cancel")
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["user"]["pending_email"] is None
    db_session.refresh(user)
    assert user.email == "cancel.auth@example.com"


def test_email_change_cancel_via_token(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    user = register_player(
        db_session,
        display_name="Cancel Token",
        email="cancel.token@example.com",
        phone="+5511999887713",
        password="password1234",
        birth_date=date(1995, 1, 1),
    )
    user.email_verified_at = datetime.utcnow()
    db_session.commit()
    raw, _, pending = request_email_change(
        db_session,
        user,
        current_password="password1234",
        new_email="cancel.token.new@example.com",
    )
    assert pending and raw

    r = api_client.post("/api/v1/auth/email-change/cancel", json={"token": raw})
    assert r.status_code == 200, r.text
    assert (
        db_session.query(EmailChangeToken)
        .filter(EmailChangeToken.user_id == user.id, EmailChangeToken.used_at.is_(None))
        .count()
        == 0
    )
    db_session.refresh(user)
    assert user.email == "cancel.token@example.com"


def test_email_change_rejects_wrong_password(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    user = register_player(
        db_session,
        display_name="Bad Pass",
        email="bad.pass@example.com",
        phone="+5511999887714",
        password="password1234",
        birth_date=date(1995, 1, 1),
    )
    user.email_verified_at = datetime.utcnow()
    db_session.commit()
    _login(api_client, user.email)

    r = api_client.post(
        "/api/v1/auth/me/email-change",
        json={"current_password": "wrong-password", "new_email": "other@example.com"},
    )
    assert r.status_code == 400


def test_phone_change_clears_verified_at(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    user = register_player(
        db_session,
        display_name="Phone Change",
        email="phone.change@example.com",
        phone="+5511999887715",
        password="password1234",
        birth_date=date(1995, 1, 1),
    )
    user.phone_verified_at = datetime.utcnow()
    db_session.commit()
    _login(api_client, user.email)

    r = api_client.patch("/api/v1/auth/me", json={"phone": "+5511999887799"})
    assert r.status_code == 200, r.text
    assert r.json()["phone"] == "5511999887799"
    assert r.json()["phone_verified_at"] is None
    db_session.refresh(user)
    assert user.phone_verified_at is None
