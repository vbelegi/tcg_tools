"""Drop handling."""

from __future__ import annotations

from app.core.torneios.scores import wins_to_win


class DropError(ValueError):
    pass


def apply_mid_round_drop(
    score_p1: int,
    score_p2: int,
    dropped_is_p1: bool,
    best_of: int,
) -> tuple[int, int]:
    """WO: remaining player gets wins_to_win-0."""
    w = wins_to_win(best_of)
    if dropped_is_p1:
        return 0, w
    return w, 0


def validate_drop_mid_round(event_status: str, has_active_round: bool) -> None:
    """Drop tipo B — durante rodada ativa."""
    if event_status != "running":
        raise DropError("Drop mid-round só em torneio em andamento.")
    if not has_active_round:
        raise DropError("Nenhuma rodada ativa. Use drop entre rodadas.")


def validate_drop_between_rounds(event_status: str, has_active_round: bool) -> None:
    """Drop tipo A — entre rodadas (sem rodada ativa)."""
    if event_status != "running":
        raise DropError("Drop entre rodadas só em torneio em andamento.")
    if has_active_round:
        raise DropError("Rodada ativa: use drop mid-round ou conclua a rodada antes.")
