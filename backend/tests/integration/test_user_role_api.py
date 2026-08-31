"""Admin user role changes (staff ↔ player)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_incomplete_user
from app.models import User, UserRole


def _create_player(db: Session, *, email: str, name: str) -> User:
    return create_incomplete_user(
        db,
        display_name=name,
        email=email,
        phone="+5511999000001",
        role=UserRole.player.value,
    )


def test_admin_promotes_player_to_staff(api_client: TestClient, db_session: Session):
    player = _create_player(db_session, email="promote@example.com", name="Promote Me")
    r = api_client.patch(f"/api/v1/users/{player.id}/role", json={"role": "staff"})
    assert r.status_code == 200
    assert r.json()["role"] == "staff"
    refreshed = db_session.query(User).filter(User.id == player.id).one()
    assert refreshed.role == UserRole.staff.value


def test_admin_demotes_staff_to_player(api_client: TestClient, db_session: Session):
    staff = create_incomplete_user(
        db_session,
        display_name="Staff Down",
        email="staff.down@example.com",
        phone="+5511999000002",
        role=UserRole.staff.value,
    )
    r = api_client.patch(f"/api/v1/users/{staff.id}/role", json={"role": "player"})
    assert r.status_code == 200
    assert r.json()["role"] == "player"


def test_cannot_change_own_role(api_client: TestClient, db_session: Session):
    admin = db_session.query(User).filter(User.email == "admin@local").one()
    r = api_client.patch(f"/api/v1/users/{admin.id}/role", json={"role": "player"})
    assert r.status_code == 403


def test_cannot_set_admin_via_patch(api_client: TestClient, db_session: Session):
    player = _create_player(db_session, email="no-admin@example.com", name="No Admin")
    r = api_client.patch(f"/api/v1/users/{player.id}/role", json={"role": "admin"})
    assert r.status_code == 400


def test_cannot_change_admin_user_role(api_client: TestClient, db_session: Session):
    from app.core.auth import hash_password

    other_admin = User(
        email="other.admin@example.com",
        display_name="Other Admin",
        phone="+5511999000099",
        role=UserRole.admin.value,
        status="active",
        password_hash=hash_password("secret"),
    )
    db_session.add(other_admin)
    db_session.commit()
    db_session.refresh(other_admin)

    r = api_client.patch(f"/api/v1/users/{other_admin.id}/role", json={"role": "staff"})
    assert r.status_code == 400
