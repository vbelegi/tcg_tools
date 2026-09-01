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
            "password": "abcdefgh12",
            "birth_date": "1995-03-20",
        },
    )
    assert r.status_code == 200
    assert r.json()["email"] == "jogador.x@example.com"

    api_client.post("/api/v1/auth/logout")
    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "jogador.x@example.com", "password": "abcdefgh12"},
    )
    assert login.status_code == 200


def test_invite_api_returns_claim_url(api_client: TestClient, db_session: Session, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("TCGTOOLS_PUBLIC_BASE_URL", "https://torneios.example.com")
    get_settings.cache_clear()
    user = create_incomplete_user(
        db_session,
        display_name="Convite URL",
        email="convite.url@example.com",
        phone="+5511999990009",
        role=UserRole.player.value,
    )
    r = api_client.post(f"/api/v1/users/{user.id}/invite")
    assert r.status_code == 200
    body = r.json()
    assert body["claim_path"] == f"/convite/{body['token']}"
    assert body["claim_url"] == f"https://torneios.example.com/convite/{body['token']}"
    get_settings.cache_clear()


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
            "tcg_game_id": 1,
        },
    )
    eid = r.json()["id"]
    from tests.conftest import enroll_named_players_api

    enroll_named_players_api(api_client, eid, ("A", "B", "C"))
    pending = api_client.post(
        f"/api/v1/torneios/{eid}/jogadores",
        json={
            "name": "D",
            "attendance": "pending",
            "create_account": True,
            "email": f"d.pending.{eid}@api.test",
            "phone": f"+55117{eid % 10000:04d}0001",
        },
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
            "tcg_game_id": 1,
        },
    )
    eid = r.json()["id"]
    names = [("A", user.id), ("B", None), ("C", None), ("D", None)]
    for i, (name, uid) in enumerate(names):
        body: dict = {"name": name}
        if uid:
            body["user_id"] = uid
        else:
            body["create_account"] = True
            body["email"] = f"{name.lower()}.fp.{eid}.{i}@api.test"
            body["phone"] = f"+55116{eid % 10000:04d}{i:04d}"
        assert api_client.post(f"/api/v1/torneios/{eid}/jogadores", json=body).status_code == 200

    assert api_client.post(f"/api/v1/torneios/{eid}/iniciar").status_code == 200
    svc = TorneioService(db_session)
    score_all_matches(svc, eid, 1)
    assert api_client.post(f"/api/v1/torneios/{eid}/avancar").status_code == 200
    assert api_client.post(f"/api/v1/torneios/{eid}/finalizar").status_code == 200

    assert db_session.query(FoursePointsLedger).filter_by(event_id=eid).count() >= 1
    assert user_fp_total(db_session, user.id) > 0

    ranking = api_client.get("/api/v1/ranking")
    assert ranking.status_code == 200
    rows = ranking.json()
    assert isinstance(rows, list) and len(rows) >= 1
    assert {"rank", "user_id", "display_name", "points", "avatar_url"} <= set(rows[0].keys())


def test_external_torneio_creates_fp(api_client: TestClient, db_session: Session):
    r = api_client.post(
        "/api/v1/torneios/externos",
        json={
            "name": "Loja Vizinha",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
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
            "tcg_game_id": 1,
        },
    )
    assert r.status_code == 200
    eid = r.json()["id"]
    assert api_client.delete(f"/api/v1/torneios/{eid}").status_code == 204
    assert api_client.get(f"/api/v1/torneios/{eid}").status_code == 404


def test_create_torneio_rejects_invalid_tcg_without_orphan(api_client: TestClient):
    before = {t["id"] for t in api_client.get("/api/v1/torneios").json()}
    bad = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Orphan TCG",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 999999,
        },
    )
    assert bad.status_code == 422
    after = {t["id"] for t in api_client.get("/api/v1/torneios").json()}
    assert after == before


def test_add_player_rejects_nameless_walk_in(api_client: TestClient):
    r = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "No Walkin",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
        },
    )
    assert r.status_code == 200
    eid = r.json()["id"]
    denied = api_client.post(f"/api/v1/torneios/{eid}/jogadores", json={"name": "Solo"})
    assert denied.status_code == 422


def test_guest_sees_finished_and_open_registration(api_client: TestClient):
    closed = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Draft Closed",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
            "registration_open": False,
        },
    )
    assert closed.status_code == 200
    closed_id = closed.json()["id"]

    open_reg = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Draft Open",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 15,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
            "registration_open": True,
        },
    )
    assert open_reg.status_code == 200
    open_id = open_reg.json()["id"]

    external = api_client.post(
        "/api/v1/torneios/externos",
        json={
            "name": "Finished Public",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
            "entry_fee": 10,
            "placements": [
                {"placement": 1, "display_name": "A"},
                {"placement": 2, "display_name": "B"},
                {"placement": 3, "display_name": "C"},
                {"placement": 4, "display_name": "D"},
            ],
        },
    )
    assert external.status_code == 200, external.text
    finished_id = external.json()["id"]

    assert api_client.post("/api/v1/auth/logout").status_code == 200

    listed = api_client.get("/api/v1/torneios")
    assert listed.status_code == 200
    ids = {e["id"] for e in listed.json()}
    assert finished_id in ids
    assert open_id in ids
    assert closed_id not in ids

    cal = api_client.get(f"/api/v1/calendar?year={date.today().year}&month={date.today().month}")
    assert cal.status_code == 200
    cal_ids = {t["id"] for t in cal.json()["tournaments"]}
    assert closed_id in cal_ids
    closed_row = next(t for t in cal.json()["tournaments"] if t["id"] == closed_id)
    assert closed_row["registration_open"] is False

    assert api_client.get(f"/api/v1/torneios/{closed_id}").status_code == 404
    assert api_client.get(f"/api/v1/torneios/{open_id}").status_code == 200
    assert api_client.get(f"/api/v1/torneios/{finished_id}").status_code == 200
    assert api_client.get(f"/api/v1/torneios/{finished_id}/classificacao").status_code == 200
    clf = api_client.get(f"/api/v1/torneios/{finished_id}/classificacao").json()
    assert isinstance(clf, dict)
    assert "standings" in clf
    assert isinstance(clf["standings"], list)
    assert api_client.get(f"/api/v1/torneios/{closed_id}/classificacao").status_code == 404


def test_player_sees_finished_enrolled_or_open_registration(
    api_client: TestClient, db_session: Session
):
    from app.core.auth import register_player

    player = register_player(
        db_session,
        display_name="Belegi",
        email="belegi.player@example.com",
        phone="+5511999990099",
        password="abcdefgh12",
        birth_date=date(1990, 1, 1),
    )

    other = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Other Draft",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
            "registration_open": False,
        },
    )
    assert other.status_code == 200
    other_id = other.json()["id"]

    open_reg = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Open For Signup",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
            "registration_open": True,
        },
    )
    assert open_reg.status_code == 200
    open_id = open_reg.json()["id"]

    mine = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "My Draft",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
        },
    )
    assert mine.status_code == 200
    mine_id = mine.json()["id"]
    assert (
        api_client.post(
            f"/api/v1/torneios/{mine_id}/jogadores",
            json={"name": "Belegi", "user_id": player.id},
        ).status_code
        == 200
    )

    finished = api_client.post(
        "/api/v1/torneios/externos",
        json={
            "name": "Finished For Player",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
            "entry_fee": 10,
            "placements": [
                {"placement": 1, "display_name": "A"},
                {"placement": 2, "display_name": "B"},
                {"placement": 3, "display_name": "C"},
                {"placement": 4, "display_name": "D"},
            ],
        },
    )
    assert finished.status_code == 200, finished.text
    finished_id = finished.json()["id"]

    assert api_client.post("/api/v1/auth/logout").status_code == 200
    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "belegi.player@example.com", "password": "abcdefgh12"},
    )
    assert login.status_code == 200

    listed = api_client.get("/api/v1/torneios")
    assert listed.status_code == 200
    ids = {e["id"] for e in listed.json()}
    assert mine_id in ids
    assert finished_id in ids
    assert open_id in ids
    assert other_id not in ids

    assert api_client.get(f"/api/v1/torneios/{mine_id}").status_code == 200
    assert api_client.get(f"/api/v1/torneios/{open_id}").status_code == 200
    assert api_client.get(f"/api/v1/torneios/{other_id}").status_code == 404
    assert api_client.get(f"/api/v1/torneios/{finished_id}").status_code == 200

    ins = api_client.post(f"/api/v1/torneios/{open_id}/inscrever")
    assert ins.status_code == 200, ins.text
