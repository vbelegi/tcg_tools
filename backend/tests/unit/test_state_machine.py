"""State machine validation tests."""

import pytest

from app.core.torneios.models import PlayerRecord, TournamentState
from app.core.torneios.state_machine import (
    StateMachineError,
    validate_complete_round,
    validate_finalize,
    validate_reopen_round,
    validate_start,
    validate_start_next_round,
)


def _state(status: str = "draft", players: int = 4) -> TournamentState:
    return TournamentState(
        event_id=1,
        format="swiss",
        best_of=3,
        max_rounds=3,
        current_round=0,
        status=status,
        shuffle_seed=1,
        players=[
            PlayerRecord(id=i, name=f"P{i}", seed=i, registration_order=i)
            for i in range(1, players + 1)
        ],
        matches=[],
    )


def test_validate_start_requires_draft():
    validate_start(_state("draft"))
    with pytest.raises(StateMachineError, match="iniciado"):
        validate_start(_state("running"))


def test_validate_start_min_players():
    with pytest.raises(StateMachineError, match="4"):
        validate_start(_state(players=3))


def test_validate_start_allows_all_unseeded():
    state = _state(players=4)
    for p in state.players:
        p.seed = None
    validate_start(state)


def test_validate_start_rejects_partial_seeds():
    state = _state(players=4)
    state.players[1].seed = None
    state.players[3].seed = None
    with pytest.raises(StateMachineError, match="Seeding parcial"):
        validate_start(state)


def test_validate_complete_round_running_only():
    validate_complete_round(_state("running"))
    with pytest.raises(StateMachineError):
        validate_complete_round(_state("draft"))


def test_validate_start_next_round_running_only():
    validate_start_next_round(_state("running"))
    with pytest.raises(StateMachineError):
        validate_start_next_round(_state("finished"))


def test_validate_finalize_running_only():
    validate_finalize(_state("running"))
    with pytest.raises(StateMachineError):
        validate_finalize(_state("finished"))


def test_validate_reopen_round_running_only():
    validate_reopen_round(_state("running"))
    with pytest.raises(StateMachineError, match="andamento"):
        validate_reopen_round(_state("finished"))
