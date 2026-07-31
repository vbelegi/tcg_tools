"""Event state machine."""

from __future__ import annotations

from app.core.torneios.models import TournamentState

VALID_TRANSITIONS = {
    "draft": {"running"},
    "running": {"running", "finished"},
    "finished": {"finished"},
}


class StateMachineError(ValueError):
    pass


def can_transition(current: str, target: str) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())


def validate_start(state: TournamentState) -> None:
    if state.status != "draft":
        raise StateMachineError("Torneio já iniciado.")
    active = [p for p in state.players if not p.dropped_at]
    if len(active) < 4:
        raise StateMachineError("Mínimo de 4 jogadores para iniciar.")


def validate_complete_round(state: TournamentState) -> None:
    if state.status != "running":
        raise StateMachineError("Torneio não está em andamento.")


def validate_start_next_round(state: TournamentState) -> None:
    if state.status != "running":
        raise StateMachineError("Torneio não está em andamento.")


def validate_finalize(state: TournamentState) -> None:
    if state.status != "running":
        raise StateMachineError("Torneio não está em andamento.")


def validate_reopen_round(state: TournamentState) -> None:
    if state.status != "running":
        raise StateMachineError("Só é possível reabrir rodadas com torneio em andamento.")
