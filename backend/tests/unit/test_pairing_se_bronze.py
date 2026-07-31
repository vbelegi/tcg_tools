"""Bronze pairing unit test."""

from __future__ import annotations

from app.core.torneios.models import MatchRecord, PlayerRecord, TournamentState
from app.core.torneios.pairing.pairing_se import SingleEliminationStrategy


def test_bronze_pairing_on_final_round():
    players = [
        PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i) for i in range(1, 5)
    ]
    matches = [
        MatchRecord(1, 1, 1, 2, 1, 0, False, False, False, True, 1),
        MatchRecord(2, 1, 3, 4, 1, 0, False, False, False, True, 3),
        MatchRecord(3, 2, 1, 3, 1, 0, False, False, False, True, 1),
    ]
    state = TournamentState(
        event_id=1,
        format="single_elimination",
        best_of=1,
        max_rounds=2,
        current_round=1,
        status="running",
        shuffle_seed=1,
        players=players,
        matches=matches,
        third_place_match=True,
    )
    pairings = SingleEliminationStrategy().generate_pairings(state, 2)
    assert len(pairings) == 2
    bronze = [p for p in pairings if p.is_third_place]
    assert len(bronze) == 1
    assert bronze[0].player1_id == 2
    assert bronze[0].player2_id == 4
