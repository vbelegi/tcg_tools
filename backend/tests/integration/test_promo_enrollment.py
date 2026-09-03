"""Promotional action enrolment: single-use QR, 10-minute guest cookie, verify-email promotion."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_email_verification, register_player
from app.core.promo.enrollment import ENROLL_COOKIE
from app.models import PromoEnrollmentToken, PromoParticipant, PromoParticipantStatus

from tests.integration.test_promo_actions_api import _create


def _token_from_path(path: str) -> str:
    assert path.startswith("/acoes/participar/")
    return path.rsplit("/", 1)[-1]


def _issue(client: TestClient, action_id: int) -> tuple[str, dict]:
    r = client.post(f"/api/v1/acoes/{action_id}/enrollment-token")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["path"].startswith("/acoes/participar/")
    assert body["expires_in_seconds"] == 600
    return _token_from_path(body["path"]), body


def _verified_player(db: Session, client: TestClient, suffix: str) -> dict:
    user = register_player(
        db,
        display_name=f"Player {suffix}",
        email=f"enroll.{suffix}@example.com",
        phone=f"+5511988{int(suffix):05d}",
        password="password1234",
        birth_date=date(1990, 1, 1),
    )
    user.email_verified_at = datetime.utcnow()
    db.commit()
    client.post("/api/v1/auth/logout")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "password1234"},
    )
    assert login.status_code == 200, login.text
    return {"id": user.id, "email": user.email}


def test_logged_in_verified_user_is_confirmed(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    raw, _ = _issue(api_client, action["id"])
    _verified_player(db_session, api_client, "1001")

    first = api_client.get(f"/api/v1/acoes/enroll/{raw}")
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["reason"] == "ok"
    assert body["message"] == "Inscrição confirmada."
    assert body["participation_status"] == PromoParticipantStatus.confirmed.value

    api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    api_client.post(f"/api/v1/acoes/{action['id']}/publish")
    api_client.post(
        "/api/v1/auth/login",
        json={"email": "enroll.1001@example.com", "password": "password1234"},
    )
    detail = api_client.get(f"/api/v1/acoes/{action['id']}").json()
    assert detail["my_participation"] == {"status": "confirmed"}

    second = api_client.get(f"/api/v1/acoes/enroll/{raw}")
    assert second.status_code == 400
    assert second.json()["reason"] == "used"


def test_already_enrolled_returns_named_conflict(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    raw1, _ = _issue(api_client, action["id"])
    _verified_player(db_session, api_client, "1002")
    assert api_client.get(f"/api/v1/acoes/enroll/{raw1}").status_code == 200

    api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    raw2, _ = _issue(api_client, action["id"])
    api_client.post(
        "/api/v1/auth/login",
        json={"email": "enroll.1002@example.com", "password": "password1234"},
    )
    again = api_client.get(f"/api/v1/acoes/enroll/{raw2}")
    assert again.status_code == 409
    assert again.json()["reason"] == "already_enrolled"
    assert "já está inscrito" in again.json()["message"]


def test_guest_cookie_then_complete_after_register(
    api_client: TestClient, db_session: Session
):
    action = _create(api_client)
    raw, _ = _issue(api_client, action["id"])
    api_client.post("/api/v1/auth/logout")

    first = api_client.get(f"/api/v1/acoes/enroll/{raw}")
    assert first.status_code == 200, first.text
    assert first.json()["reason"] == "needs_auth"
    assert api_client.cookies.get(ENROLL_COOKIE)

    replay = api_client.get(f"/api/v1/acoes/enroll/{raw}")
    assert replay.status_code == 200
    assert replay.json()["reason"] == "needs_auth"

    register = api_client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Loja Guest",
            "email": "enroll.guest@example.com",
            "phone": "+5511999100300",
            "password": "password1234",
            "birth_date": "1992-02-02",
            "accept_privacy": True,
        },
    )
    assert register.status_code == 201, register.text

    pending = api_client.cookies.get(ENROLL_COOKIE)
    assert pending
    complete = api_client.post("/api/v1/acoes/enroll/complete")
    assert complete.status_code == 200, complete.text
    assert complete.json()["reason"] == "needs_verification"
    assert complete.json()["participation_status"] == "pending_verification"

    api_client.cookies.set(ENROLL_COOKIE, pending)
    again = api_client.post("/api/v1/acoes/enroll/complete")
    assert again.status_code == 200, again.text
    assert again.json()["reason"] == "needs_verification"

    user_id = register.json()["id"]
    from app.models import User

    user = db_session.query(User).filter(User.id == user_id).one()
    raw_verify, _ = create_email_verification(db_session, user)
    verified = api_client.post("/api/v1/auth/verify-email", json={"token": raw_verify})
    assert verified.status_code == 200

    row = (
        db_session.query(PromoParticipant)
        .filter(PromoParticipant.promo_id == action["id"], PromoParticipant.user_id == user_id)
        .one()
    )
    db_session.refresh(row)
    assert row.status == PromoParticipantStatus.confirmed.value


def test_complete_after_ten_minutes_expires(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    raw, _ = _issue(api_client, action["id"])
    api_client.post("/api/v1/auth/logout")
    assert api_client.get(f"/api/v1/acoes/enroll/{raw}").json()["reason"] == "needs_auth"

    row = db_session.query(PromoEnrollmentToken).one()
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()

    api_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@local", "password": "testpass12"},
    )
    late = api_client.post("/api/v1/acoes/enroll/complete")
    assert late.status_code == 400
    assert late.json()["reason"] == "expired"
    assert db_session.query(PromoParticipant).count() == 0


def test_shared_link_without_cookie_is_used(api_client: TestClient):
    action = _create(api_client)
    raw, _ = _issue(api_client, action["id"])
    api_client.post("/api/v1/auth/logout")
    assert api_client.get(f"/api/v1/acoes/enroll/{raw}").json()["reason"] == "needs_auth"

    api_client.cookies.delete(ENROLL_COOKIE)
    stolen = api_client.get(f"/api/v1/acoes/enroll/{raw}")
    assert stolen.status_code == 400
    assert stolen.json()["reason"] == "used"


def test_expired_token_on_first_access(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    raw, _ = _issue(api_client, action["id"])
    row = db_session.query(PromoEnrollmentToken).one()
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()

    api_client.post("/api/v1/auth/logout")
    r = api_client.get(f"/api/v1/acoes/enroll/{raw}")
    assert r.status_code == 400
    assert r.json()["reason"] == "expired"


def test_invalid_token(api_client: TestClient):
    api_client.post("/api/v1/auth/logout")
    r = api_client.get("/api/v1/acoes/enroll/not-a-real-token")
    assert r.status_code == 400
    assert r.json()["reason"] == "invalid"


def test_cannot_issue_or_enroll_after_end_date(api_client: TestClient):
    action = _create(
        api_client,
        start_date=(date.today() - timedelta(days=10)).isoformat(),
        end_date=(date.today() - timedelta(days=1)).isoformat(),
    )
    r = api_client.post(f"/api/v1/acoes/{action['id']}/enrollment-token")
    assert r.status_code == 400
    assert r.json()["detail"]["reason"] == "ended"


def test_max_participants_blocks_further_enrolment(api_client: TestClient, db_session: Session):
    action = _create(api_client, max_participants=1)
    raw, _ = _issue(api_client, action["id"])
    _verified_player(db_session, api_client, "1004")
    assert api_client.get(f"/api/v1/acoes/enroll/{raw}").json()["reason"] == "ok"

    api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    blocked = api_client.post(f"/api/v1/acoes/{action['id']}/enrollment-token")
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["reason"] == "full"


def test_same_user_can_join_two_actions(api_client: TestClient, db_session: Session):
    first = _create(api_client, name="Ação Um")
    second = _create(api_client, name="Ação Dois")
    raw1, _ = _issue(api_client, first["id"])
    raw2, _ = _issue(api_client, second["id"])
    _verified_player(db_session, api_client, "1005")

    assert api_client.get(f"/api/v1/acoes/enroll/{raw1}").json()["reason"] == "ok"
    assert api_client.get(f"/api/v1/acoes/enroll/{raw2}").json()["reason"] == "ok"
    assert db_session.query(PromoParticipant).count() == 2


def test_detail_hides_participation_from_guests(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    api_client.post(f"/api/v1/acoes/{action['id']}/publish")
    raw, _ = _issue(api_client, action["id"])
    player = _verified_player(db_session, api_client, "1006")
    api_client.get(f"/api/v1/acoes/enroll/{raw}")

    api_client.post("/api/v1/auth/logout")
    public = api_client.get(f"/api/v1/acoes/{action['id']}").json()
    assert "my_participation" not in public
    assert "participant_count" not in public
    assert player["id"]
