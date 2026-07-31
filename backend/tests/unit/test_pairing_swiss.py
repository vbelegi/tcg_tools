"""Unit tests for Swiss pairing."""

from __future__ import annotations

from app.core.torneios.models import MatchRecord, PlayerRecord, TournamentState
from app.core.torneios.pairing.pairing_swiss import SwissPairingStrategy


def _four_player_state() -> TournamentState:
    players = [
        PlayerRecord(id=i, name=chr(64 + i), seed=i, registration_order=i)
        for i in range(1, 5)
    ]
    return TournamentState(
        event_id=1,
        format="swiss",
        best_of=3,
        max_rounds=2,
        current_round=0,
        status="running",
        shuffle_seed=12345,
        players=players,
        matches=[],
    )


def test_round1_pairs_all_active():
    state = _four_player_state()
    pairings = SwissPairingStrategy().generate_pairings(state, 1)
    assert len(pairings) == 2
    ids = {p.player1_id for p in pairings} | {p.player2_id for p in pairings if p.player2_id}
    assert ids == {1, 2, 3, 4}


def test_round2_avoids_rematch_when_possible():
    state = _four_player_state()
    state.matches = [
        MatchRecord(
            id=1,
            round_number=1,
            player1_id=1,
            player2_id=2,
            score_p1=2,
            score_p2=0,
            is_bye=False,
            is_walkover=False,
            had_rematch=False,
            scores_submitted=True,
            winner_id=1,
        ),
        MatchRecord(
            id=2,
            round_number=1,
            player1_id=3,
            player2_id=4,
            score_p1=2,
            score_p2=0,
            is_bye=False,
            is_walkover=False,
            had_rematch=False,
            scores_submitted=True,
            winner_id=3,
        ),
    ]
    state.played_pairs = {frozenset({1, 2}), frozenset({3, 4})}
    state.current_round = 1
    pairings = SwissPairingStrategy().generate_pairings(state, 2)
    for p in pairings:
        if p.player2_id:
            assert frozenset({p.player1_id, p.player2_id}) not in state.played_pairs
            assert not p.had_rematch


def test_bye_r3_goes_to_lowest_without_prev_win():
    players = [
        PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i)
        for i in range(1, 6)
    ]
    matches = [
        MatchRecord(1, 1, 1, 2, 2, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 3, 4, 2, 0, False, False, False, True, 3),
        MatchRecord(3, 1, 5, None, 2, 0, True, False, False, True, 5),
        MatchRecord(4, 2, 1, 3, 2, 0, False, False, False, True, 1),
        MatchRecord(5, 2, 2, 4, 0, 2, False, False, False, True, 4),
    ]
    state = TournamentState(
        event_id=1,
        format="swiss",
        best_of=3,
        max_rounds=3,
        current_round=2,
        status="running",
        shuffle_seed=1,
        players=players,
        matches=matches,
        played_pairs={frozenset({1, 2}), frozenset({3, 4}), frozenset({1, 3}), frozenset({2, 4})},
    )
    pairings = SwissPairingStrategy().generate_pairings(state, 3)
    bye = next(p for p in pairings if p.is_bye)
    assert bye.player1_id == 2


def test_round3_cross_bracket_avoids_rematch():
    """Top bracket already played — downpair/uppair before rematch."""
    players = [
        PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i)
        for i in range(1, 6)
    ]
    matches = [
        MatchRecord(1, 1, 1, 2, 2, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 3, 4, 2, 0, False, False, False, True, 3),
        MatchRecord(3, 1, 5, None, 2, 0, True, False, False, True, 5),
        MatchRecord(4, 2, 1, 3, 2, 0, False, False, False, True, 1),
        MatchRecord(5, 2, 2, 4, 0, 2, False, False, False, True, 4),
    ]
    state = TournamentState(
        event_id=1,
        format="swiss",
        best_of=3,
        max_rounds=3,
        current_round=2,
        status="running",
        shuffle_seed=1,
        players=players,
        matches=matches,
        played_pairs={frozenset({1, 2}), frozenset({3, 4}), frozenset({1, 3}), frozenset({2, 4})},
    )
    pairings = [p for p in SwissPairingStrategy().generate_pairings(state, 3) if not p.is_bye]
    assert len(pairings) == 2
    for p in pairings:
        assert frozenset({p.player1_id, p.player2_id}) not in state.played_pairs
        assert not p.had_rematch


def test_rematch_only_when_unavoidable():
    """Four players who already played everyone — rematch is last resort."""
    players = [
        PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i)
        for i in range(1, 5)
    ]
    played = {frozenset({a, b}) for a in range(1, 5) for b in range(a + 1, 5)}
    state = TournamentState(
        event_id=1,
        format="swiss",
        best_of=3,
        max_rounds=4,
        current_round=3,
        status="running",
        shuffle_seed=1,
        players=players,
        matches=[
            MatchRecord(1, 1, 1, 2, 2, 0, False, False, False, True, 1),
            MatchRecord(2, 1, 3, 4, 2, 0, False, False, False, True, 3),
            MatchRecord(3, 2, 1, 3, 2, 0, False, False, False, True, 1),
            MatchRecord(4, 2, 2, 4, 2, 0, False, False, False, True, 2),
            MatchRecord(5, 3, 1, 4, 2, 0, False, False, False, True, 1),
            MatchRecord(6, 3, 2, 3, 2, 0, False, False, False, True, 2),
        ],
        played_pairs=played,
    )
    pairings = SwissPairingStrategy().generate_pairings(state, 4)
    rematches = [p for p in pairings if p.had_rematch and p.player2_id]
    assert len(rematches) >= 1
    for p in pairings:
        if p.player2_id and not p.had_rematch:
            assert frozenset({p.player1_id, p.player2_id}) not in state.played_pairs


def test_nine_players_round3_prefers_cross_bracket_over_rematch():
    """Scenario similar to production: 9 players, R3 should avoid rematch when possible."""
    players = [
        PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i)
        for i in range(1, 10)
    ]
    matches = [
        # R1
        MatchRecord(1, 1, 1, 2, 2, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 3, 4, 2, 0, False, False, False, True, 3),
        MatchRecord(3, 1, 5, 6, 2, 0, False, False, False, True, 5),
        MatchRecord(4, 1, 7, 8, 2, 0, False, False, False, True, 7),
        MatchRecord(5, 1, 9, None, 2, 0, True, False, False, True, 9),
        # R2
        MatchRecord(6, 2, 1, 3, 2, 0, False, False, False, True, 1),
        MatchRecord(7, 2, 5, 7, 2, 0, False, False, False, True, 5),
        MatchRecord(8, 2, 2, 4, 2, 0, False, False, False, True, 2),
        MatchRecord(9, 2, 6, 8, 2, 0, False, False, False, True, 6),
        MatchRecord(10, 2, 9, None, 2, 0, True, False, False, True, 9),
    ]
    played = {
        frozenset({1, 2}),
        frozenset({3, 4}),
        frozenset({5, 6}),
        frozenset({7, 8}),
        frozenset({1, 3}),
        frozenset({5, 7}),
        frozenset({2, 4}),
        frozenset({6, 8}),
    }
    state = TournamentState(
        event_id=1,
        format="swiss",
        best_of=3,
        max_rounds=3,
        current_round=2,
        status="running",
        shuffle_seed=42,
        players=players,
        matches=matches,
        played_pairs=played,
    )
    pairings = [p for p in SwissPairingStrategy().generate_pairings(state, 3) if p.player2_id]
    assert all(not p.had_rematch for p in pairings)
    for p in pairings:
        assert frozenset({p.player1_id, p.player2_id}) not in played

