"""Integration tests for torneios API with real Alembic DB."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.services.torneio_service import TorneioService
from tests.conftest import enroll_named_players_api, run_se_bracket, score_all_matches


def _create_swiss(client: TestClient) -> int:
    r = client.post(
        "/api/v1/torneios",
        json={
            "name": "API Swiss",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 35,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
        },
    )
    assert r.status_code == 200
    eid = r.json()["id"]
    enroll_named_players_api(client, eid, ("A", "B", "C", "D"))
    return eid


def test_create_and_list(api_client: TestClient):
    eid = _create_swiss(api_client)
    r = api_client.get("/api/v1/torneios")
    assert r.status_code == 200
    assert any(t["id"] == eid for t in r.json())


def test_full_round_lifecycle(api_client: TestClient, db_session):
    eid = _create_swiss(api_client)
    assert api_client.post(f"/api/v1/torneios/{eid}/iniciar").status_code == 200

    svc = TorneioService(db_session)
    score_all_matches(svc, eid, 1, [(2, 0), (2, 0)])

    r = api_client.post(f"/api/v1/torneios/{eid}/avancar")
    assert r.status_code == 200
    assert r.json()["between_rounds"] is True

    r = api_client.post(f"/api/v1/torneios/{eid}/iniciar-proxima-rodada")
    assert r.status_code == 200
    assert r.json()["current_round"] == 2

    score_all_matches(svc, eid, 2)
    assert api_client.post(f"/api/v1/torneios/{eid}/avancar").status_code == 200
    r = api_client.post(f"/api/v1/torneios/{eid}/finalizar")
    assert r.status_code == 200
    assert r.json()["status"] == "finished"


def test_reabrir_rodada_api(api_client: TestClient, db_session):
    eid = _create_swiss(api_client)
    api_client.post(f"/api/v1/torneios/{eid}/iniciar")
    svc = TorneioService(db_session)
    score_all_matches(svc, eid, 1, [(2, 0), (2, 0)])
    api_client.post(f"/api/v1/torneios/{eid}/avancar")
    api_client.post(f"/api/v1/torneios/{eid}/iniciar-proxima-rodada")

    r = api_client.post(f"/api/v1/torneios/{eid}/rodadas/reabrir")
    assert r.status_code == 200
    body = r.json()
    assert body["current_round"] == 1
    assert body["between_rounds"] is False


def test_drop_between_rounds_422_during_active(api_client: TestClient, db_session):
    eid = _create_swiss(api_client)
    api_client.post(f"/api/v1/torneios/{eid}/iniciar")
    detail = api_client.get(f"/api/v1/torneios/{eid}").json()
    pid = detail["players"][0]["id"]
    r = api_client.post(
        f"/api/v1/torneios/{eid}/jogadores/{pid}/drop",
        json={"mid_round": False},
    )
    assert r.status_code == 422


def _create_se(client: TestClient, player_count: int = 4) -> int:
    r = client.post(
        "/api/v1/torneios",
        json={
            "name": "API SE",
            "event_date": date.today().isoformat(),
            "format": "single_elimination",
            "max_rounds": None,
            "entry_fee": 35,
            "best_of": 1,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
            "third_place_match": True,
            "se_bo_config": {"1": 3, "2": 1},
        },
    )
    assert r.status_code == 200
    eid = r.json()["id"]
    enroll_named_players_api(client, eid, [f"P{i + 1}" for i in range(player_count)])
    return eid


def test_se_api_full_flow(api_client: TestClient, db_session):
    eid = _create_se(api_client, 4)

    svc = TorneioService(db_session)
    run_se_bracket(svc, eid, default=(1, 0))

    r = api_client.post(f"/api/v1/torneios/{eid}/finalizar")
    assert r.status_code == 200
    assert r.json()["status"] == "finished"

    prem = api_client.get(f"/api/v1/torneios/{eid}/premiacao").json()
    assert prem["schema_version"] == 2
    assert prem["bands"] is not None
    assert prem["total_creditos"] == 140.0


def test_create_se_invalid_bo_config(api_client: TestClient):
    r = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Bad SE",
            "event_date": date.today().isoformat(),
            "format": "single_elimination",
            "max_rounds": None,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
            "se_bo_config": {"1": 7},
        },
    )
    assert r.status_code == 422


def test_finalize_rejected_with_active_round(api_client: TestClient):
    eid = _create_swiss(api_client)
    api_client.post(f"/api/v1/torneios/{eid}/iniciar")
    r = api_client.post(f"/api/v1/torneios/{eid}/finalizar")
    assert r.status_code == 422


def test_list_torneios_filters_by_name_date_and_active(api_client: TestClient, db_session):
    from app.models import Event

    early = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Aberto Alpha",
            "event_date": "2026-09-05",
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
        },
    )
    assert early.status_code == 200
    late = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Encerrado Beta",
            "event_date": "2026-09-20",
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
        },
    )
    assert late.status_code == 200
    late_id = late.json()["id"]
    row = db_session.query(Event).filter(Event.id == late_id).one()
    row.status = "finished"
    db_session.commit()

    by_name = api_client.get("/api/v1/torneios", params={"q": "alpha"}).json()
    assert [t["id"] for t in by_name] == [early.json()["id"]]

    by_range = api_client.get(
        "/api/v1/torneios",
        params={"from": "2026-09-01", "to": "2026-09-10"},
    ).json()
    assert {t["id"] for t in by_range} == {early.json()["id"]}

    active_only = api_client.get("/api/v1/torneios", params={"active": "true"}).json()
    active_ids = {t["id"] for t in active_only}
    assert early.json()["id"] in active_ids
    assert late_id not in active_ids
