"""Event state machine."""

from __future__ import annotations

from app.core.torneios.models import PlayerRecord, TournamentState

VALID_TRANSITIONS = {
    "draft": {"running"},
    "running": {"running", "finished"},
    "finished": {"finished"},
}


class StateMachineError(ValueError):
    pass


def can_transition(current: str, target: str) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())


def players_missing_seed(players: list[PlayerRecord]) -> list[PlayerRecord]:
    """Se alguém tem seed, retorna quem está sem (all-or-nothing)."""
    has_any = any(p.seed is not None for p in players)
    if not has_any:
        return []
    return [p for p in players if p.seed is None]


def validate_seeds_all_or_nothing(players: list[PlayerRecord]) -> None:
    missing = players_missing_seed(players)
    if not missing:
        return
    names = ", ".join(p.name for p in missing)
    raise StateMachineError(
        "Seeding parcial: informe seed para todos os jogadores, ou deixe todos sem seed. "
        f"Faltando seed: {names}."
    )


def validate_start(state: TournamentState) -> None:
    if state.status != "draft":
        raise StateMachineError("Torneio já iniciado.")
    active = [p for p in state.players if not p.dropped_at]
    if len(active) < 4:
        raise StateMachineError("Mínimo de 4 jogadores para iniciar.")
    validate_seeds_all_or_nothing(active)


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
