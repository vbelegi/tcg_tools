"""Additional torneio service and API coverage."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.models import Event, Match, Player, Round
from app.services.torneio_service import TorneioError, TorneioService
from tests.conftest import score_all_matches


def test_export_log_after_finalize(torneio_service: TorneioService, swiss_event, tmp_path, monkeypatch):
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()

    svc = TorneioService(torneio_service._db)
    eid = swiss_event.id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1)
    svc.complete_round(eid)
    svc.start_next_round(eid)
    score_all_matches(svc, eid, 2)
    svc.complete_round(eid)
    svc.finalize(eid)

    content, filename = svc.export_log(eid)
    assert b'"standings"' in content
    assert b'"version": 2' in content
    assert filename.endswith(".json")
    logs_dir = get_settings().resolved_logs_dir
    assert (logs_dir / filename).exists()


def test_get_classificacao_running(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1)
    svc.complete_round(eid)
    rows = svc.get_classificacao(eid)
    assert len(rows) == 4
    assert all("rank" in r for r in rows)


def test_update_event_draft_only(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.update_event(eid, {"name": "Renamed"})
    assert svc.get_event(eid)["name"] == "Renamed"
    svc.update_event(eid, {"entry_fee": 25.0, "event_date": date(2099, 6, 15)})
    updated = svc.get_event(eid)
    assert updated["entry_fee"] == 25.0
    assert updated["event_date"] == "2099-06-15"
    svc.start_event(eid)
    with pytest.raises(TorneioError, match="rascunho"):
        svc.update_event(eid, {"name": "X"})


def test_same_name_different_dates_allowed(torneio_service: TorneioService):
    svc = torneio_service
    today = date.today()
    e1 = svc.create_event(
        name="Semanal Pokémon",
        event_date=today,
        format="swiss",
        max_rounds=2,
        entry_fee=10,
        best_of=3,
        premiacao_preset_id="standard",
    )
    e2 = svc.create_event(
        name="Semanal Pokémon",
        event_date=today + timedelta(days=7),
        format="swiss",
        max_rounds=2,
        entry_fee=10,
        best_of=3,
        premiacao_preset_id="standard",
    )
    assert e1.id != e2.id


def test_same_name_same_date_rejected(torneio_service: TorneioService):
    svc = torneio_service
    today = date.today()
    svc.create_event(
        name="Semanal Pokémon",
        event_date=today,
        format="swiss",
        max_rounds=2,
        entry_fee=10,
        best_of=3,
        premiacao_preset_id="standard",
    )
    with pytest.raises(TorneioError, match="na data"):
        svc.create_event(
            name="semanal pokémon",
            event_date=today,
            format="swiss",
            max_rounds=2,
            entry_fee=10,
            best_of=3,
            premiacao_preset_id="standard",
        )


def test_update_event_name_date_conflict(torneio_service: TorneioService):
    svc = torneio_service
    today = date.today()
    e1 = svc.create_event(
        name="Torneio A",
        event_date=today,
        format="swiss",
        max_rounds=2,
        entry_fee=10,
        best_of=3,
        premiacao_preset_id="standard",
    )
    other_day = today + timedelta(days=7)
    e2 = svc.create_event(
        name="Torneio B",
        event_date=other_day,
        format="swiss",
        max_rounds=2,
        entry_fee=10,
        best_of=3,
        premiacao_preset_id="standard",
    )
    with pytest.raises(TorneioError, match="na data"):
        svc.update_event(e2.id, {"name": "Torneio A", "event_date": today})
    svc.update_event(e1.id, {"name": "Torneio A Renomeado"})
    assert svc.get_event(e1.id)["name"] == "Torneio A Renomeado"


def test_finalize_manual_placements(torneio_service: TorneioService):
    svc = torneio_service
    today = date.today()
    event = svc.create_event(
        name="Manual Mode",
        event_date=today,
        format="swiss",
        max_rounds=2,
        entry_fee=10,
        best_of=3,
        premiacao_preset_id="standard",
    )
    event.pairing_mode = "manual"
    svc._commit()
    from tests.conftest import enroll_named_players

    enroll_named_players(svc, event.id, ("A", "B", "C", "D"))
    players = svc.get_event(event.id)["players"]
    placements = [
        {"player_id": players[0]["id"], "placement": 1, "is_drop": False},
        {"player_id": players[1]["id"], "placement": 2, "is_drop": False},
        {"player_id": players[2]["id"], "placement": 3, "is_drop": False},
        {"player_id": players[3]["id"], "placement": 4, "is_drop": True},
    ]
    svc.finalize_manual_placements(event.id, placements)
    finished = svc.get_event(event.id)
    assert finished["status"] == "finished"
    assert finished["pairing_mode"] == "manual"
    assert svc._require_event(event.id).premiacao_resultado is not None


def test_manual_mode_blocks_start_event(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    event = svc._require_event(swiss_event.id)
    event.pairing_mode = "manual"
    svc._commit()
    with pytest.raises(TorneioError, match="sem rodadas"):
        svc.start_event(swiss_event.id)


def test_update_pairing_mode_in_draft(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.update_event(eid, {"pairing_mode": "manual"})
    assert svc.get_event(eid)["pairing_mode"] == "manual"
    svc.update_event(eid, {"pairing_mode": "platform"})
    assert svc.get_event(eid)["pairing_mode"] == "platform"


def test_remove_player_draft(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    pid = svc.get_event(eid)["players"][0]["id"]
    svc.remove_player(eid, pid)
    assert len(svc.get_event(eid)["players"]) == 3


def test_create_event_invalid_format(torneio_service: TorneioService):
    with pytest.raises(TorneioError, match="Formato"):
        torneio_service.create_event(
            name="X",
            event_date=date.today(),
            format="invalid",
            max_rounds=2,
            entry_fee=10,
            best_of=3,
            premiacao_preset_id="standard",
        )


def test_reopen_round_not_found(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.start_event(eid)
    with pytest.raises(TorneioError, match="concluídas"):
        svc.reopen_round(eid, round_number=1)


def test_walkover_match_not_editable():
    db = MagicMock()
    repo = MagicMock()
    event = Event(
        id=1,
        name="T",
        event_date=date.today(),
        format="swiss",
        max_rounds=2,
        entry_fee=10,
        best_of=3,
        premiacao_preset={"label": "T"},
        status="running",
        shuffle_seed=1,
    )
    m = Match(
        id=1,
        round_id=1,
        player1_id=1,
        player2_id=2,
        is_walkover=True,
        is_bye=False,
        had_rematch=False,
        scores_submitted=True,
        score_p1=2,
        score_p2=0,
        winner_id=1,
    )
    event.players = [
        Player(id=1, event_id=1, name="A", seed=1, registration_order=1),
        Player(id=2, event_id=1, name="B", seed=2, registration_order=2),
    ]
    event.rounds = [Round(id=1, event_id=1, number=1, status="active", matches=[m])]
    repo.get.return_value = event

    svc = TorneioService(db, repo=repo)
    with pytest.raises(TorneioError, match="WO"):
        svc.update_match(1, 1, 0, 2)
