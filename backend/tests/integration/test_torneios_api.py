"""Integration tests for torneios API with real Alembic DB."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.services.torneio_service import TorneioService
from tests.conftest import run_se_bracket, score_all_matches


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
    for name in ("A", "B", "C", "D"):
        assert client.post(f"/api/v1/torneios/{eid}/jogadores", json={"name": name}).status_code == 200
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
    for i in range(player_count):
        assert (
            client.post(
                f"/api/v1/torneios/{eid}/jogadores",
                json={"name": f"P{i + 1}"},
            ).status_code
            == 200
        )
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
