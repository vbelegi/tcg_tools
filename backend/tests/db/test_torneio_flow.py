"""Full tournament flow against Alembic-migrated SQLite (production-like)."""

from __future__ import annotations

from datetime import date

import pytest

from app.services.torneio_service import TorneioError, TorneioService
from tests.conftest import score_all_matches


def test_create_and_start_tournament(torneio_service: TorneioService, swiss_event):
    event = torneio_service.start_event(swiss_event.id)
    detail = torneio_service.get_event(event.id)
    assert detail["status"] == "running"
    assert detail["current_round"] == 1
    assert detail["between_rounds"] is False


def test_swiss_full_flow_finalize(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.start_event(eid)

    score_all_matches(svc, eid, 1, [(2, 0), (2, 0)])
    svc.complete_round(eid)
    detail = svc.get_event(eid)
    assert detail["between_rounds"] is True
    assert detail["can_start_next_round"] is True

    svc.start_next_round(eid)
    rnd2 = svc.get_round(eid, 2)
    assert rnd2["player_records"]
    player_ids = {
        pid
        for m in rnd2["matches"]
        for pid in (m["player1_id"], m["player2_id"])
        if pid is not None
    }
    for pid in player_ids:
        rec = rnd2["player_records"][pid]
        assert set(rec) == {"wins", "losses", "draws"}
        assert rec["wins"] + rec["losses"] + rec["draws"] == 1
    score_all_matches(svc, eid, 2)
    svc.complete_round(eid)

    detail = svc.get_event(eid)
    assert detail["can_finalize"] is True
    svc.finalize(eid)
    assert svc.get_event(eid)["status"] == "finished"
    assert svc.get_premiacao(eid)["premiados"] >= 3


def test_reopen_between_rounds(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1, [(2, 0), (2, 0)])
    svc.complete_round(eid)

    svc.reopen_round(eid)
    detail = svc.get_event(eid)
    assert detail["current_round"] == 1
    assert detail["between_rounds"] is False

    rnd = svc.get_round(eid, 1)
    assert rnd["status"] == "active"
    non_bye = [m for m in rnd["matches"] if not m["is_bye"]]
    svc.update_match(eid, non_bye[0]["id"], 0, 2)
    score_all_matches(svc, eid, 1, [(0, 2), (2, 0)])
    svc.complete_round(eid)
    assert svc.get_event(eid)["between_rounds"] is True


def test_reopen_deletes_active_next_round(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1, [(2, 0), (2, 0)])
    svc.complete_round(eid)
    svc.start_next_round(eid)
    assert svc.get_event(eid)["current_round"] == 2

    svc.reopen_round(eid)
    detail = svc.get_event(eid)
    assert detail["current_round"] == 1
    rounds = svc.get_rounds(eid)
    assert len(rounds) == 1
    assert rounds[0]["number"] == 1
    assert rounds[0]["status"] == "active"


def test_reopen_then_repair_pairing(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1, [(2, 0), (2, 0)])
    svc.complete_round(eid)
    svc.start_next_round(eid)
    r2_before = svc.get_round(eid, 2)
    pairs_before = {
        frozenset({m["player1_id"], m["player2_id"]})
        for m in r2_before["matches"]
        if not m["is_bye"]
    }

    svc.reopen_round(eid)
    score_all_matches(svc, eid, 1, [(2, 1), (0, 2)])
    svc.complete_round(eid)
    svc.start_next_round(eid)
    r2_after = svc.get_round(eid, 2)
    pairs_after = {
        frozenset({m["player1_id"], m["player2_id"]})
        for m in r2_after["matches"]
        if not m["is_bye"]
    }
    assert pairs_before != pairs_after


def test_reopen_rejected_when_finished(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1, [(2, 0), (2, 0)])
    svc.complete_round(eid)
    svc.start_next_round(eid)
    score_all_matches(svc, eid, 2)
    svc.complete_round(eid)
    svc.finalize(eid)

    with pytest.raises(TorneioError, match="andamento"):
        svc.reopen_round(eid)


def test_finalize_rejected_with_incomplete_scores(torneio_service: TorneioService, swiss_event):
    svc = torneio_service
    eid = swiss_event.id
    svc.start_event(eid)
    with pytest.raises(TorneioError, match="resultados"):
        svc.complete_round(eid)
