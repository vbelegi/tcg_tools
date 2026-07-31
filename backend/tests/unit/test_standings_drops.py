"""Standings drop row tests."""

from __future__ import annotations

from datetime import datetime

from app.core.torneios.models import MatchRecord, PlayerRecord, TournamentState
from app.core.torneios.standings import compute_standings


def test_dropped_players_at_bottom_with_drop_label():
    players = [
        PlayerRecord(id=1, name="A", seed=1, registration_order=1),
        PlayerRecord(id=2, name="B", seed=2, registration_order=2, dropped_at=datetime.utcnow()),
        PlayerRecord(id=3, name="C", seed=3, registration_order=3),
        PlayerRecord(id=4, name="D", seed=4, registration_order=4, dropped_at=datetime.utcnow()),
    ]
    matches = [
        MatchRecord(1, 1, 1, 3, 1, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 4, None, 2, 0, True, False, False, True, 4),
    ]
    state = TournamentState(
        event_id=1,
        format="swiss",
        best_of=3,
        max_rounds=2,
        current_round=1,
        status="running",
        shuffle_seed=99,
        players=players,
        matches=matches,
    )
    rows = compute_standings(state)
    drops = [r for r in rows if r.is_drop]
    assert len(drops) == 2
    assert all(r.rank_label == "DROP" for r in drops)
    assert rows[-1].is_drop
    assert rows[-2].is_drop
