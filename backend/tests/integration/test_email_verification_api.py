"""Email verification and forgot-password flows."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_email_verification, register_player
from app.core.rate_limit import reset_rate_limits_for_tests
from app.models import EmailVerificationToken


def test_register_sends_verification_and_me_shows_unverified(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    r = api_client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Verify Test",
            "email": "verify.test@example.com",
            "phone": "+5511999887701",
            "password": "password1234",
            "birth_date": "1995-05-05",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email_verified"] is False

    me = api_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email_verified"] is False

    row = (
        db_session.query(EmailVerificationToken)
        .filter(EmailVerificationToken.user_id == body["id"])
        .one()
    )


def test_verify_email_marks_user_verified(api_client: TestClient, db_session: Session):
    user = register_player(
        db_session,
        display_name="To Verify",
        email="to.verify@example.com",
        phone="+5511999887702",
        password="password1234",
        birth_date=date(1995, 1, 1),
    )
    raw, _ = create_email_verification(db_session, user)
    api_client.post("/api/v1/auth/logout")

    r = api_client.post("/api/v1/auth/verify-email", json={"token": raw})
    assert r.status_code == 200, r.text
    assert r.json()["email_verified"] is True

    db_session.refresh(user)
    assert user.email_verified_at is not None


def test_resend_verification_rate_limit(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    register_player(
        db_session,
        display_name="Resend",
        email="resend@example.com",
        phone="+5511999887703",
        password="password1234",
        birth_date=date(1995, 1, 1),
    )
    api_client.post(
        "/api/v1/auth/login",
        json={"email": "resend@example.com", "password": "password1234"},
    )
    first = api_client.post("/api/v1/auth/resend-verification")
    assert first.status_code == 200, first.text
    second = api_client.post("/api/v1/auth/resend-verification")
    assert second.status_code == 429


def test_forgot_password_generic_for_unknown_email(api_client: TestClient):
    reset_rate_limits_for_tests()
    r = api_client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r.status_code == 200
    assert "Se existir" in r.json()["message"]


def test_forgot_password_sends_only_when_verified(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    user = register_player(
        db_session,
        display_name="Forgot",
        email="forgot@example.com",
        phone="+5511999887704",
        password="password1234",
        birth_date=date(1995, 1, 1),
    )
    api_client.post("/api/v1/auth/logout")

    r = api_client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    assert r.status_code == 200
    from app.models import PasswordResetToken

    assert db_session.query(PasswordResetToken).filter_by(user_id=user.id).count() == 0

    user.email_verified_at = user.created_at
    db_session.commit()
    reset_rate_limits_for_tests()
    r2 = api_client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    assert r2.status_code == 200
    assert db_session.query(PasswordResetToken).filter_by(user_id=user.id).count() == 1


def test_claim_invite_sets_email_verified(api_client: TestClient, db_session: Session):
    from app.core.auth import create_incomplete_user, create_invite

    user = create_incomplete_user(
        db_session,
        display_name="Invite Verified",
        email="invite.verified@example.com",
        phone="+5511999887705",
    )
    invite = create_invite(db_session, user)
    api_client.post("/api/v1/auth/logout")

    r = api_client.post(
        "/api/v1/auth/claim-invite",
        json={
            "token": invite.token,
            "password": "password1234",
            "birth_date": "1990-01-01",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["email_verified"] is True
