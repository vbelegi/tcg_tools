"""Unit tests for SE standings."""

from __future__ import annotations

from app.core.torneios.models import MatchRecord, PlayerRecord, TournamentState
from app.core.torneios.se_bands import format_band_label
from app.core.torneios.standings.se import compute_se_standings


def _state(
    players: list[PlayerRecord],
    matches: list[MatchRecord],
    *,
    max_rounds: int = 2,
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


def test_se_4_players_final_standings():
    players = [
        PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i) for i in range(1, 5)
    ]
    matches = [
        MatchRecord(1, 1, 1, 2, 1, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 3, 4, 1, 0, False, False, False, True, 3),
        MatchRecord(3, 2, 1, 3, 1, 0, False, False, False, True, 1),
    ]
    rows = compute_se_standings(_state(players, matches, max_rounds=2))
    labels = {r.player_id: r.rank_label for r in rows if not r.is_drop}
    assert labels[1] == "1º"
    assert labels[3] == "2º"
    assert labels[2] == format_band_label(3, 4)
    assert labels[4] == format_band_label(3, 4)


def test_se_bronze_standings():
    players = [
        PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i) for i in range(1, 5)
    ]
    matches = [
        MatchRecord(1, 1, 1, 2, 1, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 3, 4, 1, 0, False, False, False, True, 3),
        MatchRecord(3, 2, 1, 3, 1, 0, False, False, False, True, 1),
        MatchRecord(
            4, 2, 2, 4, 1, 0, False, False, False, True, 2, is_third_place=True
        ),
    ]
    rows = compute_se_standings(
        _state(players, matches, max_rounds=2, third_place_match=True)
    )
    labels = {r.player_id: r.rank_label for r in rows if not r.is_drop}
    assert labels[1] == "1º"
    assert labels[3] == "2º"
    assert labels[2] == "3º"
    assert labels[4] == "4º"
