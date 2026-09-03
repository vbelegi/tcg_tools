"""Staff panel for promotional actions: participants list and per-action logs."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import hash_password
from app.models import User, UserRole, UserStatus
from tests.integration.test_promo_actions_api import _create
from tests.integration.test_promo_enrollment import _issue, _verified_player


def _login_staff(db: Session, client: TestClient) -> User:
    staff = User(
        email="staff.panel@example.com",
        display_name="Staff Loja",
        phone="+5511999000400",
        role=UserRole.staff.value,
        status=UserStatus.active.value,
        password_hash=hash_password("password1234"),
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": staff.email, "password": "password1234"},
    )
    assert r.status_code == 200, r.text
    return staff


def test_participants_are_staff_only_and_hide_contact(
    api_client: TestClient, db_session: Session
):
    action = _create(api_client)
    raw, _ = _issue(api_client, action["id"])
    player = _verified_player(db_session, api_client, "1401")
    assert api_client.get(f"/api/v1/acoes/enroll/{raw}").json()["reason"] == "ok"

    forbidden = api_client.get(f"/api/v1/acoes/{action['id']}/participants")
    assert forbidden.status_code == 403

    api_client.post("/api/v1/auth/logout")
    anon = api_client.get(f"/api/v1/acoes/{action['id']}/participants")
    assert anon.status_code == 401

    api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    staff_ok = api_client.get(f"/api/v1/acoes/{action['id']}/participants")
    assert staff_ok.status_code == 200, staff_ok.text
    body = staff_ok.json()
    assert len(body) == 1
    assert body[0]["display_name"] == "Player 1401"
    assert body[0]["status"] == "confirmed"
    assert "email" not in body[0]
    assert "phone" not in body[0]
    assert player["email"] not in staff_ok.text


def test_logs_are_admin_only(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    api_client.patch(f"/api/v1/acoes/{action['id']}", json={"description": "Atualizado"})

    admin_logs = api_client.get(f"/api/v1/acoes/{action['id']}/logs")
    assert admin_logs.status_code == 200, admin_logs.text
    actions = {row["action"] for row in admin_logs.json()}
    assert "promo.create" in actions
    assert "promo.edit" in actions
    assert all(row["meta"]["promo_id"] == action["id"] for row in admin_logs.json())

    _login_staff(db_session, api_client)
    staff_logs = api_client.get(f"/api/v1/acoes/{action['id']}/logs")
    assert staff_logs.status_code == 403

    api_client.post("/api/v1/auth/logout")
    assert api_client.get(f"/api/v1/acoes/{action['id']}/logs").status_code == 401


def test_staff_can_list_participants(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    raw, _ = _issue(api_client, action["id"])
    _verified_player(db_session, api_client, "1402")
    api_client.get(f"/api/v1/acoes/enroll/{raw}")

    _login_staff(db_session, api_client)
    r = api_client.get(f"/api/v1/acoes/{action['id']}/participants")
    assert r.status_code == 200
    assert r.json()[0]["display_name"] == "Player 1402"
