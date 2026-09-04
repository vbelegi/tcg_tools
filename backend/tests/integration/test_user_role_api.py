"""Admin/superadmin user role changes with password confirmation."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_incomplete_user, hash_password
from app.models import User, UserRole, UserStatus


ADMIN_PASS = "testpass12"


def _create_player(db: Session, *, email: str, name: str, phone: str) -> User:
    return create_incomplete_user(
        db,
        display_name=name,
        email=email,
        phone=phone,
        role=UserRole.player.value,
    )


def test_bootstrap_admin_is_superadmin(api_client: TestClient, db_session: Session):
    admin = db_session.query(User).filter(User.email == "admin@local").one()
    assert admin.role == UserRole.superadmin.value
    me = api_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["role"] == "superadmin"


def test_promotes_player_to_staff_with_password(api_client: TestClient, db_session: Session):
    player = _create_player(
        db_session, email="promote@example.com", name="Promote Me", phone="+5511999000001"
    )
    r = api_client.patch(
        f"/api/v1/users/{player.id}/role",
        json={"role": "staff", "current_password": ADMIN_PASS},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "staff"


def test_role_change_requires_password(api_client: TestClient, db_session: Session):
    player = _create_player(
        db_session, email="need.pass@example.com", name="Need Pass", phone="+5511999000011"
    )
    r = api_client.patch(f"/api/v1/users/{player.id}/role", json={"role": "staff"})
    assert r.status_code == 422
    bad = api_client.patch(
        f"/api/v1/users/{player.id}/role",
        json={"role": "staff", "current_password": "wrong-password"},
    )
    assert bad.status_code == 400


def test_admin_cannot_grant_admin(api_client: TestClient, db_session: Session):
    bootstrap = db_session.query(User).filter(User.email == "admin@local").one()
    bootstrap.role = UserRole.admin.value
    db_session.commit()

    player = _create_player(
        db_session, email="no-admin@example.com", name="No Admin", phone="+5511999000012"
    )
    r = api_client.patch(
        f"/api/v1/users/{player.id}/role",
        json={"role": "admin", "current_password": ADMIN_PASS},
    )
    assert r.status_code == 403


def test_superadmin_can_grant_admin(api_client: TestClient, db_session: Session):
    player = _create_player(
        db_session, email="to-admin@example.com", name="To Admin", phone="+5511999000013"
    )
    r = api_client.patch(
        f"/api/v1/users/{player.id}/role",
        json={"role": "admin", "current_password": ADMIN_PASS},
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "admin"


def test_cannot_change_own_role(api_client: TestClient, db_session: Session):
    admin = db_session.query(User).filter(User.email == "admin@local").one()
    r = api_client.patch(
        f"/api/v1/users/{admin.id}/role",
        json={"role": "player", "current_password": ADMIN_PASS},
    )
    assert r.status_code == 403


def test_superadmin_demotes_another_superadmin(api_client: TestClient, db_session: Session):
    other = User(
        email="second.sa@example.com",
        display_name="Second SA",
        phone="+5511999000088",
        role=UserRole.superadmin.value,
        status=UserStatus.active.value,
        password_hash=hash_password("secret1234"),
    )
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    r = api_client.patch(
        f"/api/v1/users/{other.id}/role",
        json={"role": "admin", "current_password": ADMIN_PASS},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_cannot_delete_last_superadmin_via_self(api_client: TestClient, db_session: Session):
    r = api_client.post(
        "/api/v1/auth/me/delete",
        json={"password": ADMIN_PASS, "confirm": "EXCLUIR"},
    )
    assert r.status_code == 400
    assert "Super Admin" in r.json()["detail"]


def test_admin_cannot_change_admin_target(api_client: TestClient, db_session: Session):
    bootstrap = db_session.query(User).filter(User.email == "admin@local").one()
    bootstrap.role = UserRole.admin.value
    db_session.commit()

    other_admin = User(
        email="other.admin@example.com",
        display_name="Other Admin",
        phone="+5511999000099",
        role=UserRole.admin.value,
        status=UserStatus.active.value,
        password_hash=hash_password("secret1234"),
    )
    db_session.add(other_admin)
    db_session.commit()
    db_session.refresh(other_admin)

    r = api_client.patch(
        f"/api/v1/users/{other_admin.id}/role",
        json={"role": "staff", "current_password": ADMIN_PASS},
    )
    assert r.status_code == 400


def test_audit_logs_list(api_client: TestClient, db_session: Session):
    player = _create_player(
        db_session, email="audited@example.com", name="Audited", phone="+5511999000014"
    )
    api_client.patch(
        f"/api/v1/users/{player.id}/role",
        json={"role": "staff", "current_password": ADMIN_PASS},
    )
    r = api_client.get("/api/v1/audit-logs?action=user.role_change")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 1
    assert any(i["action"] == "user.role_change" for i in body["items"])
