"""Unit tests for OMW and standings."""

from __future__ import annotations

import pytest

from app.core.torneios.models import MatchRecord, PlayerRecord, TournamentState
from app.core.torneios.standings import compute_match_records, compute_standings
from app.core.torneios.standings.omw import oponente_bye_ficticio


def test_oponente_bye_ficticio_neutral_for_0_0_0():
    assert oponente_bye_ficticio((0, 0, 0)) == 0.33


def test_oponente_bye_ficticio_reflects_losses():
    pct = oponente_bye_ficticio((0, 2, 0))
    assert pct < oponente_bye_ficticio((0, 0, 0))
    assert pct == pytest.approx(0.0, abs=0.01)


def test_standings_r1_bye_only_uses_ficticio_neutral_omw():
    """Bye cedo (0-0-0) — OMW neutro via oponente BYE fictício."""
    players = [
        PlayerRecord(id=1, name="A", seed=1, registration_order=1),
        PlayerRecord(id=2, name="B", seed=2, registration_order=2),
        PlayerRecord(id=3, name="C", seed=3, registration_order=3),
    ]
    matches = [
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
            player2_id=None,
            score_p1=2,
            score_p2=0,
            is_bye=True,
            is_walkover=False,
            had_rematch=False,
            scores_submitted=True,
            winner_id=3,
        ),
    ]
    state = TournamentState(
        event_id=1,
        format="swiss",
        best_of=3,
        max_rounds=2,
        current_round=1,
        status="running",
        shuffle_seed=1,
        players=players,
        matches=matches,
        played_pairs={frozenset({1, 2})},
    )
    standings = compute_standings(state)
    p3 = next(s for s in standings if s.player_id == 3)
    assert p3.omw == pytest.approx(0.33, abs=0.01)


def test_compute_match_records_before_round():
    players = [
        PlayerRecord(id=1, name="A", seed=1, registration_order=1),
        PlayerRecord(id=2, name="B", seed=2, registration_order=2),
        PlayerRecord(id=3, name="C", seed=3, registration_order=3),
    ]
    matches = [
        MatchRecord(1, 1, 1, 2, 2, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 3, None, 2, 0, True, False, False, True, 3),
        MatchRecord(3, 2, 1, 3, 2, 0, False, False, False, True, 1),
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
    )
    entering_r2 = compute_match_records(state, before_round=2)
    assert entering_r2[1] == {"wins": 1, "losses": 0, "draws": 0}
    assert entering_r2[2] == {"wins": 0, "losses": 1, "draws": 0}
    assert entering_r2[3] == {"wins": 1, "losses": 0, "draws": 0}

    entering_r3 = compute_match_records(state, before_round=3)
    assert entering_r3[1] == {"wins": 2, "losses": 0, "draws": 0}
    assert entering_r3[3] == {"wins": 1, "losses": 1, "draws": 0}
