"""Security hardening: calendar visibility, rate limit, session hash."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_session, get_user_for_token
from app.core.auth.session_tokens import hash_session_token
from app.core.rate_limit import reset_rate_limits_for_tests
from app.models import Session as AuthSession
from app.services.torneio_service import TorneioService


def test_calendar_hides_closed_draft_from_anonymous(
    db_session: Session, torneio_service: TorneioService,
):
    from app.core.auth import upsert_admin_password
    from app.db.session import get_db
    from app.main import app

    upsert_admin_password(db_session, "testpass12")
    event = torneio_service.create_event(
        name="Secret Draft",
        event_date=date.today(),
        format="swiss",
        max_rounds=2,
        entry_fee=10.0,
        best_of=3,
        premiacao_preset_id="standard",
    )
    torneio_service.update_event(event.id, {"registration_open": False})

    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    today = date.today()
    r = client.get(f"/api/v1/calendar?year={today.year}&month={today.month}")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()["tournaments"]]
    assert event.id not in ids

    torneio_service.update_event(event.id, {"registration_open": True})
    r2 = client.get(f"/api/v1/calendar?year={today.year}&month={today.month}")
    ids2 = [t["id"] for t in r2.json()["tournaments"]]
    assert event.id in ids2
    app.dependency_overrides.clear()


def test_session_token_stored_hashed(db_session: Session):
    from app.core.auth import upsert_admin_password
    from app.models import User

    upsert_admin_password(db_session, "testpass12")
    user = db_session.query(User).filter(User.email == "admin@local").one()
    token = create_session(db_session, user)
    row = db_session.query(AuthSession).one()
    assert row.token == hash_session_token(token)
    assert row.token != token
    assert get_user_for_token(db_session, token) is not None
    assert get_user_for_token(db_session, "wrong-token") is None


def test_login_revokes_previous_session(api_client: TestClient, db_session: Session):
    from app.core.auth import upsert_admin_password
    from app.core.auth.service import SESSION_COOKIE
    from app.models import User

    upsert_admin_password(db_session, "testpass12")
    r1 = api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    assert r1.status_code == 200
    cookie1 = api_client.cookies.get(SESSION_COOKIE)

    r2 = api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    assert r2.status_code == 200
    cookie2 = api_client.cookies.get(SESSION_COOKIE)
    assert cookie1 != cookie2

    api_client.cookies.set(SESSION_COOKIE, cookie1)
    assert api_client.get("/api/v1/auth/me").status_code == 401

    api_client.cookies.set(SESSION_COOKIE, cookie2)
    assert api_client.get("/api/v1/auth/me").status_code == 200


def test_login_rate_limit(api_client: TestClient, db_session: Session):
    from app.core.auth import upsert_admin_password

    reset_rate_limits_for_tests()
    upsert_admin_password(db_session, "testpass12")
    for _ in range(10):
        api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "wrong"})
    blocked = api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "wrong"})
    assert blocked.status_code == 429
    reset_rate_limits_for_tests()
