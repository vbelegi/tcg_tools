"""Torneio service tests with mock repository."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.core.torneios.models import PlayerRecord, TournamentState
from app.models import Event, Match, Player, Round
from app.services.torneio_service import TorneioError, TorneioService


def _draft_event() -> Event:
    event = Event(
        id=1,
        name="Test",
        event_date=date.today(),
        format="swiss",
        max_rounds=2,
        entry_fee=10.0,
        best_of=3,
        premiacao_preset={
            "label": "T",
            "min_jogadores": 4,
            "min_premiados": 3,
            "max_premiados": 8,
            "crescimento": 4,
            "r": 0.72,
            "casas_decimais": 2,
        },
        status="draft",
        shuffle_seed=1,
    )
    event.players = [
        Player(id=i, event_id=1, name=f"P{i}", seed=i, registration_order=i)
        for i in range(1, 5)
    ]
    event.rounds = []
    return event


def test_drop_between_rounds_when_no_active_round():
    db = MagicMock()
    repo = MagicMock()
    event = _draft_event()
    event.status = "running"
    event.rounds = [Round(id=1, event_id=1, number=1, status="completed", matches=[])]
    player = event.players[0]
    repo.get.return_value = event

    svc = TorneioService(db, repo=repo)
    svc.drop_player(1, player.id, mid_round=False)
    assert player.dropped_at is not None
    repo.commit.assert_called()


def test_drop_between_rounds_rejected_during_active_round():
    db = MagicMock()
    repo = MagicMock()
    event = _draft_event()
    event.status = "running"
    event.rounds = [Round(id=1, event_id=1, number=1, status="active", matches=[])]
    repo.get.return_value = event

    svc = TorneioService(db, repo=repo)
    with pytest.raises(TorneioError, match="Rodada ativa"):
        svc.drop_player(1, event.players[0].id, mid_round=False)
    repo.rollback.assert_called()


def test_finalize_rejected_with_active_round():
    db = MagicMock()
    repo = MagicMock()
    event = _draft_event()
    event.status = "running"
    m = Match(
        id=1,
        round_id=1,
        player1_id=1,
        player2_id=2,
        score_p1=1,
        score_p2=0,
        is_bye=False,
        is_walkover=False,
        had_rematch=False,
        scores_submitted=True,
        winner_id=1,
    )
    event.rounds = [Round(id=1, event_id=1, number=1, status="active", matches=[m])]
    repo.get.return_value = event
    repo.to_tournament_state.return_value = TournamentState(
        event_id=1,
        format="swiss",
        best_of=3,
        max_rounds=2,
        current_round=1,
        status="running",
        shuffle_seed=1,
        players=[
            PlayerRecord(id=p.id, name=p.name, seed=p.seed, registration_order=p.registration_order)
            for p in event.players
        ],
        matches=[],
    )

    svc = TorneioService(db, repo=repo)
    with pytest.raises(TorneioError, match="finalizar"):
        svc.finalize(1)


def test_duplicate_player_name_rejected():
    db = MagicMock()
    repo = MagicMock()
    event = _draft_event()
    repo.get.return_value = event

    svc = TorneioService(db, repo=repo)
    with pytest.raises(TorneioError, match="P1"):
        svc.add_player(1, "P1")
