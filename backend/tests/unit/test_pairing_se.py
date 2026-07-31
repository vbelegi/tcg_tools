"""Unit tests for single elimination pairing."""

from __future__ import annotations

from app.core.torneios.models import PlayerRecord, TournamentState
from app.core.torneios.pairing.pairing_se import SingleEliminationStrategy


def test_six_players_seeded_get_two_byes_for_highest_seeds():
    players = [
        PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i)
        for i in range(1, 7)
    ]
    state = TournamentState(
        event_id=1,
        format="single_elimination",
        best_of=3,
        max_rounds=3,
        current_round=0,
        status="running",
        shuffle_seed=99,
        players=players,
        matches=[],
    )
    pairings = SingleEliminationStrategy().generate_pairings(state, 1)
    byes = [p for p in pairings if p.is_bye]
    assert len(byes) == 2
    bye_ids = sorted(p.player1_id for p in byes)
    assert bye_ids == [1, 2]


def test_five_players_unseeded_gets_one_bye():
    players = [
        PlayerRecord(id=i, name=f"P{i}", seed=None, registration_order=i)
        for i in range(1, 6)
    ]
    state = TournamentState(
        event_id=1,
        format="single_elimination",
        best_of=3,
        max_rounds=3,
        current_round=0,
        status="running",
        shuffle_seed=42,
        players=players,
        matches=[],
    )
    pairings = SingleEliminationStrategy().generate_pairings(state, 1)
    assert len(pairings) == 3
    assert sum(1 for p in pairings if p.is_bye) == 1
