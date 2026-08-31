"""Session cookie and invite URL unit tests."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.auth import upsert_admin_password
from app.core.auth.invites import invite_claim_path, invite_claim_url
from app.core.auth.passwords import ADMIN_EMAIL
from app.db.session import get_db
from app.main import app


def test_resolved_cookie_secure_from_https_base(monkeypatch):
    monkeypatch.setenv("TCGTOOLS_PUBLIC_BASE_URL", "https://torneios.example.com")
    monkeypatch.delenv("TCGTOOLS_COOKIE_SECURE", raising=False)
    get_settings.cache_clear()
    assert get_settings().resolved_cookie_secure is True
    get_settings.cache_clear()


def test_resolved_cookie_secure_false_without_https(monkeypatch):
    monkeypatch.delenv("TCGTOOLS_PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("TCGTOOLS_COOKIE_SECURE", raising=False)
    get_settings.cache_clear()
    assert get_settings().resolved_cookie_secure is False
    get_settings.cache_clear()


def test_login_sets_secure_cookie_when_https_base(db_session: Session, monkeypatch):
    monkeypatch.setenv("TCGTOOLS_PUBLIC_BASE_URL", "https://torneios.example.com")
    get_settings.cache_clear()
    upsert_admin_password(db_session, "abcdefgh12")

    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    r = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "abcdefgh12"})
    assert r.status_code == 200
    cookie = r.headers.get("set-cookie", "")
    assert "Secure" in cookie
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_invite_claim_url_uses_public_base(monkeypatch):
    monkeypatch.setenv("TCGTOOLS_PUBLIC_BASE_URL", "https://torneios.fourse.com.br")
    get_settings.cache_clear()
    assert invite_claim_path("abc123") == "/convite/abc123"
    assert invite_claim_url("abc123") == "https://torneios.fourse.com.br/convite/abc123"
    get_settings.cache_clear()


def test_invite_claim_url_none_without_base(monkeypatch):
    monkeypatch.delenv("TCGTOOLS_PUBLIC_BASE_URL", raising=False)
    get_settings.cache_clear()
    assert invite_claim_url("abc123") is None
    get_settings.cache_clear()
