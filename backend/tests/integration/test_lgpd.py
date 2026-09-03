"""LGPD: privacy accept, marketing opt-out, export contacts, account delete."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_incomplete_user, create_invite, register_player
from app.core.auth.account_lifecycle import delete_user_account, purge_stale_incomplete
from app.core.privacy import ANONYMOUS_DISPLAY_NAME, can_contact_for_marketing
from app.core.rate_limit import reset_rate_limits_for_tests
from app.models import Player, StaffAuditLog, User, UserStatus
from app.services.torneio_service import TorneioService


def test_register_requires_privacy_accept(api_client: TestClient):
    reset_rate_limits_for_tests()
    r = api_client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "No Privacy",
            "email": "noprivacy@example.com",
            "phone": "+5511999000011",
            "password": "password1234",
            "birth_date": "1990-01-01",
            "accept_privacy": False,
        },
    )
    assert r.status_code == 400


def test_marketing_opt_out_excludes_from_export(api_client: TestClient, db_session: Session):
    reset_rate_limits_for_tests()
    from app.core.auth import upsert_admin_password

    upsert_admin_password(db_session, "testpass12")
    user = register_player(
        db_session,
        display_name="Contactable",
        email="contactable@example.com",
        phone="+5511999000022",
        password="password1234",
        birth_date=date(1990, 1, 1),
    )
    assert can_contact_for_marketing(user) is True

    api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    r = api_client.get("/api/v1/users/export-contacts")
    assert r.status_code == 200
    assert "Contactable" in r.text
    assert "+5511999000022" in r.text or "5511999000022" in r.text

    user.marketing_opt_out = True
    db_session.commit()
    r2 = api_client.get("/api/v1/users/export-contacts")
    assert "Contactable" not in r2.text
    assert db_session.query(StaffAuditLog).filter_by(action="marketing.export").count() >= 1


def test_delete_account_anonymizes_players(api_client: TestClient, db_session: Session, torneio_service: TorneioService):
    user = register_player(
        db_session,
        display_name="To Delete",
        email="todelete@example.com",
        phone="+5511999000033",
        password="password1234",
        birth_date=date(1990, 1, 1),
    )
    event = torneio_service.create_event(
        name="Del Event",
        event_date=date.today(),
        format="swiss",
        max_rounds=2,
        entry_fee=10.0,
        best_of=3,
        premiacao_preset_id="standard",
    )
    player = torneio_service.add_player(event.id, user.display_name, user_id=user.id)
    assert player.name == "To Delete"

    api_client.post("/api/v1/auth/login", json={"email": "todelete@example.com", "password": "password1234"})
    r = api_client.post(
        "/api/v1/auth/me/delete",
        json={"password": "password1234", "confirm": "EXCLUIR"},
    )
    assert r.status_code == 200, r.text
    db_session.refresh(user)
    assert user.status == UserStatus.deleted.value
    db_session.refresh(player)
    assert player.name == ANONYMOUS_DISPLAY_NAME


def test_purge_stale_incomplete(db_session: Session):
    user = create_incomplete_user(
        db_session,
        display_name="Old Incomplete",
        email="old.incomplete@example.com",
        phone="+5511999000044",
    )
    user.created_at = datetime.utcnow() - timedelta(days=200)
    db_session.commit()
    ids = purge_stale_incomplete(db_session, days=180)
    assert user.id in ids
    db_session.refresh(user)
    assert user.status == UserStatus.deleted.value


def test_invite_token_is_hashed(db_session: Session):
    user = create_incomplete_user(
        db_session,
        display_name="Hash Invite",
        email="hash.invite@example.com",
        phone="+5511999000055",
    )
    raw, row = create_invite(db_session, user)
    assert raw != row.token
    assert len(row.token) == 64
