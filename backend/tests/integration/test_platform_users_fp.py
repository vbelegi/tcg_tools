"""Platform users, attendance, invites, FP ledger."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_incomplete_user, create_invite
from app.core.auth.fourse_points import user_fp_total
from app.models import FoursePointsLedger, UserRole
from app.services.torneio_service import TorneioService


def test_invite_claim_and_login(api_client: TestClient, db_session: Session):
    user = create_incomplete_user(
        db_session,
        display_name="Jogador X",
        email="jogador.x@example.com",
        phone="+5511999990001",
        role=UserRole.player.value,
    )
    invite = create_invite(db_session, user)
    r = api_client.post(
        "/api/v1/auth/claim-invite",
        json={
            "token": invite.token,
            "password": "abcdef",
            "birth_date": "1995-03-20",
        },
    )
    assert r.status_code == 200
    assert r.json()["email"] == "jogador.x@example.com"

    api_client.post("/api/v1/auth/logout")
    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "jogador.x@example.com", "password": "abcdef"},
    )
    assert login.status_code == 200


def test_pending_attendance_blocks_start(api_client: TestClient, db_session: Session):
    r = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Pending start",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
        },
    )
    eid = r.json()["id"]
    for name in ("A", "B", "C"):
        assert (
            api_client.post(f"/api/v1/torneios/{eid}/jogadores", json={"name": name}).status_code
            == 200
        )
    pending = api_client.post(
        f"/api/v1/torneios/{eid}/jogadores",
        json={"name": "D", "attendance": "pending"},
    )
    assert pending.status_code == 200
    start = api_client.post(f"/api/v1/torneios/{eid}/iniciar")
    assert start.status_code == 422

    pid = pending.json()["id"]
    assert api_client.post(f"/api/v1/torneios/{eid}/jogadores/{pid}/check-in").status_code == 200
    assert api_client.post(f"/api/v1/torneios/{eid}/iniciar").status_code == 200


def test_finalize_awards_fp(api_client: TestClient, db_session: Session):
    from tests.conftest import score_all_matches

    user = create_incomplete_user(
        db_session,
        display_name="FP Player",
        email="fp.player@example.com",
        phone="+5511999990002",
        role=UserRole.player.value,
    )
    r = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "FP Event",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 1,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
        },
    )
    eid = r.json()["id"]
    names = [("A", user.id), ("B", None), ("C", None), ("D", None)]
    for name, uid in names:
        body: dict = {"name": name}
        if uid:
            body["user_id"] = uid
        assert api_client.post(f"/api/v1/torneios/{eid}/jogadores", json=body).status_code == 200

    assert api_client.post(f"/api/v1/torneios/{eid}/iniciar").status_code == 200
    svc = TorneioService(db_session)
    score_all_matches(svc, eid, 1)
    assert api_client.post(f"/api/v1/torneios/{eid}/avancar").status_code == 200
    assert api_client.post(f"/api/v1/torneios/{eid}/finalizar").status_code == 200

    assert db_session.query(FoursePointsLedger).filter_by(event_id=eid).count() >= 1
    assert user_fp_total(db_session, user.id) > 0


def test_external_torneio_creates_fp(api_client: TestClient, db_session: Session):
    r = api_client.post(
        "/api/v1/torneios/externos",
        json={
            "name": "Loja Vizinha",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "premiacao_preset_id": "standard",
            "entry_fee": 20,
            "placements": [
                {
                    "placement": 1,
                    "display_name": "Alpha",
                    "email": "alpha@example.com",
                    "phone": "+5511999990003",
                    "create_account": True,
                },
                {"placement": 2, "display_name": "Beta"},
                {"placement": 3, "display_name": "Gamma"},
                {"placement": 4, "display_name": "Delta", "is_drop": True},
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source"] == "external"
    assert body["status"] == "finished"
    assert db_session.query(FoursePointsLedger).filter_by(event_id=body["id"]).count() >= 1


def test_users_search_staff(api_client: TestClient, db_session: Session):
    create_incomplete_user(
        db_session,
        display_name="Busca Teste",
        email="busca@example.com",
        phone="+5511999990004",
        role=UserRole.player.value,
    )
    r = api_client.get("/api/v1/users/search?q=Busca")
    assert r.status_code == 200
    assert any(u["email"] == "busca@example.com" for u in r.json())


def test_delete_torneio_admin(api_client: TestClient):
    r = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "To Delete",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
        },
    )
    assert r.status_code == 200
    eid = r.json()["id"]
    assert api_client.delete(f"/api/v1/torneios/{eid}").status_code == 204
    assert api_client.get(f"/api/v1/torneios/{eid}").status_code == 404
