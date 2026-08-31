"""Auth unit/API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import authenticate, upsert_admin_password
from app.core.auth.passwords import ADMIN_EMAIL, AuthError, hash_password, verify_password
from app.main import app
from app.db.session import get_db


def test_hash_and_verify():
    h = hash_password("secret1234")
    assert verify_password("secret1234", h)
    assert not verify_password("wrong", h)


def test_password_min_length():
    with pytest.raises(AuthError, match="10"):
        hash_password("123456789")


def test_upsert_and_login(db_session: Session):
    upsert_admin_password(db_session, "abcdefgh12")
    user = authenticate(db_session, ADMIN_EMAIL, "abcdefgh12")
    assert user.email == ADMIN_EMAIL
    user2 = authenticate(db_session, "admin", "abcdefgh12")
    assert user2.id == user.id
    with pytest.raises(AuthError):
        authenticate(db_session, ADMIN_EMAIL, "wrongxx")


def test_auth_api_flow(db_session: Session):
    upsert_admin_password(db_session, "abcdefgh12")

    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    assert client.get("/api/v1/torneios").status_code == 200  # public list
    assert client.post("/api/v1/torneios", json={}).status_code in (401, 422)
    assert client.get("/api/v1/auth/status").json()["configured"] is True
    r = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "abcdefgh12"})
    assert r.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.get("/api/v1/premiacao/presets").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/premiacao/presets").status_code == 401
    app.dependency_overrides.clear()


def test_register_player_api(db_session: Session):
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    r = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Novo Player",
            "email": "novo.player@example.com",
            "phone": "+5511988776655",
            "password": "abcdefgh12",
            "birth_date": "1990-05-15",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["role"] == "player"
    assert client.get("/api/v1/auth/me").status_code == 200
    app.dependency_overrides.clear()


def test_register_minor_requires_guardian(db_session: Session):
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    r = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Menor",
            "email": "menor@example.com",
            "phone": "+5511988776611",
            "password": "abcdefgh12",
            "birth_date": "2015-01-01",
        },
    )
    assert r.status_code == 400
    r2 = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Menor",
            "email": "menor@example.com",
            "phone": "+5511988776611",
            "password": "abcdefgh12",
            "birth_date": "2015-01-01",
            "guardian_name": "Pai",
            "guardian_phone": "+5511988776622",
        },
    )
    assert r2.status_code == 201, r2.text
    app.dependency_overrides.clear()
