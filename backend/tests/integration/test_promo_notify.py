"""Transactional update e-mails for promotional actions."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import StaffAuditLog, User
from tests.integration.test_promo_actions_api import PDF, _create
from tests.integration.test_promo_enrollment import _issue, _verified_player


def _enroll_player(client: TestClient, db: Session, action_id: int, suffix: str) -> dict:
    client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    raw, _ = _issue(client, action_id)
    player = _verified_player(db, client, suffix)
    enrolled = client.get(f"/api/v1/acoes/enroll/{raw}")
    assert enrolled.status_code == 200, enrolled.text
    client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    return player


def test_patch_end_date_emails_enrolled_users_and_audits(
    api_client: TestClient, db_session: Session, monkeypatch
):
    action = _create(api_client)
    _enroll_player(api_client, db_session, action["id"], "7001")
    sent: list[dict] = []

    def _capture(user, *, action_name, action_id, change_lines):
        sent.append(
            {
                "email": user.email,
                "action_name": action_name,
                "action_id": action_id,
                "change_lines": list(change_lines),
            }
        )

    monkeypatch.setattr("app.core.promo.notify.send_promo_update_email", _capture)

    new_end = (date.today() + timedelta(days=14)).isoformat()
    r = api_client.patch(f"/api/v1/acoes/{action['id']}", json={"end_date": new_end})
    assert r.status_code == 200, r.text
    assert len(sent) == 1
    assert sent[0]["email"] == "enroll.7001@example.com"
    assert any("Período:" in line for line in sent[0]["change_lines"])

    entry = (
        db_session.query(StaffAuditLog)
        .filter(StaffAuditLog.action == "promo.edit")
        .order_by(StaffAuditLog.id.desc())
        .first()
    )
    assert entry is not None
    assert entry.meta["promo_id"] == action["id"]


def test_publish_emails_only_when_there_are_participants(
    api_client: TestClient, db_session: Session, monkeypatch
):
    empty = _create(api_client, name="Sem inscritos")
    with_people = _create(api_client, name="Com inscritos")
    _enroll_player(api_client, db_session, with_people["id"], "7002")
    sent: list[int] = []
    monkeypatch.setattr(
        "app.core.promo.notify.send_promo_update_email",
        lambda user, **kwargs: sent.append(kwargs["action_id"]),
    )

    assert api_client.post(f"/api/v1/acoes/{empty['id']}/publish").status_code == 200
    assert empty["id"] not in sent

    assert api_client.post(f"/api/v1/acoes/{with_people['id']}/publish").status_code == 200
    assert sent.count(with_people["id"]) == 1

    sent.clear()
    assert api_client.post(f"/api/v1/acoes/{with_people['id']}/publish").status_code == 200
    assert sent == []


def test_regulation_upload_emails_participants(
    api_client: TestClient, db_session: Session, monkeypatch
):
    action = _create(api_client)
    _enroll_player(api_client, db_session, action["id"], "7003")
    sent: list[list[str]] = []
    monkeypatch.setattr(
        "app.core.promo.notify.send_promo_update_email",
        lambda user, **kwargs: sent.append(list(kwargs["change_lines"])),
    )

    upload = api_client.post(
        f"/api/v1/acoes/{action['id']}/regulamento",
        files={"file": ("reg.pdf", PDF, "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    assert sent == [["Novo regulamento (v1)."]]


def test_patch_without_real_change_does_not_email(
    api_client: TestClient, db_session: Session, monkeypatch
):
    action = _create(api_client)
    _enroll_player(api_client, db_session, action["id"], "7004")
    sent: list[int] = []
    monkeypatch.setattr(
        "app.core.promo.notify.send_promo_update_email",
        lambda user, **kwargs: sent.append(1),
    )

    r = api_client.patch(f"/api/v1/acoes/{action['id']}", json={"name": action["name"]})
    assert r.status_code == 200
    assert sent == []


def test_update_ignores_marketing_opt_out(
    api_client: TestClient, db_session: Session, monkeypatch
):
    action = _create(api_client)
    player = _enroll_player(api_client, db_session, action["id"], "7005")
    user = db_session.query(User).filter(User.id == player["id"]).one()
    user.marketing_opt_out = True
    db_session.commit()

    sent: list[str] = []
    monkeypatch.setattr(
        "app.core.promo.notify.send_promo_update_email",
        lambda user, **kwargs: sent.append(user.email),
    )
    r = api_client.patch(f"/api/v1/acoes/{action['id']}", json={"description": "Novo texto"})
    assert r.status_code == 200
    assert sent == ["enroll.7005@example.com"]
