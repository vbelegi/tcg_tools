"""Unit tests for SE bracket query helpers."""

from __future__ import annotations

from datetime import datetime

from app.core.torneios.models import MatchRecord, PlayerRecord, TournamentState
from app.core.torneios.se_bands import format_band_label
from app.core.torneios.standings.se_bracket import (
    band_label_for_elimination_round,
    bronze_match,
    final_match,
    losers_in_round,
    match_loser,
    semi_losers,
)


def _state(
    players: list[PlayerRecord],
    matches: list[MatchRecord],
    *,
    max_rounds: int = 3,
    third_place_match: bool = False,
) -> TournamentState:
    return TournamentState(
        event_id=1,
        format="single_elimination",
        best_of=1,
        max_rounds=max_rounds,
        current_round=max_rounds,
        status="running",
        shuffle_seed=1,
        players=players,
        matches=matches,
        third_place_match=third_place_match,
    )


def test_match_loser():
    m = MatchRecord(1, 3, 1, 2, 1, 0, False, False, False, True, 1)
    assert match_loser(m) == 2


def test_final_match_in_last_round():
    players = [PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i) for i in range(1, 5)]
    matches = [
        MatchRecord(1, 2, 1, 2, 1, 0, False, False, False, True, 1),
    ]
    state = _state(players, matches, max_rounds=2)
    fm = final_match(state, 2)
    assert fm is not None
    assert fm.winner_id == 1


def test_semi_losers_and_bronze():
    players = [PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i) for i in range(1, 5)]
    matches = [
        MatchRecord(1, 1, 1, 2, 1, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 3, 4, 1, 0, False, False, False, True, 3),
        MatchRecord(3, 2, 1, 3, 1, 0, False, False, False, True, 1),
        MatchRecord(4, 2, 2, 4, 1, 0, False, False, True, True, 2, is_third_place=True),
    ]
    state = _state(players, matches, max_rounds=2, third_place_match=True)
    assert sorted(semi_losers(state, 2)) == [2, 4]
    bm = bronze_match(state, 2)
    assert bm is not None
    assert bm.is_third_place is True


def test_semi_losers_empty_when_both_dropped():
    now = datetime.utcnow()
    players = [
        PlayerRecord(id=1, name="A", seed=1, registration_order=1),
        PlayerRecord(id=2, name="B", seed=2, registration_order=2, dropped_at=now),
        PlayerRecord(id=3, name="C", seed=3, registration_order=3),
        PlayerRecord(id=4, name="D", seed=4, registration_order=4, dropped_at=now),
    ]
    matches = [
        MatchRecord(1, 1, 1, 2, 1, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 3, 4, 1, 0, False, False, False, True, 3),
    ]
    state = _state(players, matches, max_rounds=2, third_place_match=True)
    assert semi_losers(state, 2) == []


def test_band_label_for_elimination_round():
    assert band_label_for_elimination_round(2, 3, False) == format_band_label(3, 4)
    assert band_label_for_elimination_round(1, 3, False) == format_band_label(5, 8)


def test_losers_in_round_excludes_byes():
    players = [PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i) for i in range(1, 7)]
    matches = [MatchRecord(1, 1, 1, 2, 1, 0, False, False, False, True, 1)]
    state = _state(players, matches, max_rounds=3)
    assert losers_in_round(state, 1) == [2]
