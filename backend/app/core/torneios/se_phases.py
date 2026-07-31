"""Best-of resolution per SE phase.

Keys in ``se_bo_config`` are ``rounds_from_final`` (1 = final, 2 = semi, …).
See ``docs/modelo_premiacao.md`` and ``docs/OPERADOR.md``.
"""

from __future__ import annotations


def rounds_from_final(round_number: int, max_rounds: int) -> int:
    """1 = final round, 2 = semifinal, etc."""
    return max_rounds - round_number + 1


def normalize_se_bo_config(raw: dict[str, int] | dict[int, int] | None) -> dict[int, int] | None:
    if raw is None:
        return None
    return {int(k): int(v) for k, v in raw.items()}


def resolve_best_of(
    round_number: int,
    max_rounds: int,
    se_bo_config: dict[int, int] | None,
    default: int,
) -> int:
    """Resolve Bo for a round; omitted phases inherit nearest lower depth, else default."""
    if not se_bo_config:
        return default
    depth = rounds_from_final(round_number, max_rounds)
    if depth in se_bo_config:
        return se_bo_config[depth]
    for d in sorted(se_bo_config.keys(), reverse=True):
        if d < depth:
            return se_bo_config[d]
    return default


def audit_se_bo_config(
    se_bo_config: dict[int, int] | None,
    max_rounds: int,
) -> tuple[dict[int, int] | None, list[str]]:
    """Drop phases beyond ``max_rounds``; return pruned config and human warnings."""
    if not se_bo_config:
        return None, []
    warnings: list[str] = []
    pruned: dict[int, int] = {}
    for depth in sorted(se_bo_config.keys()):
        bo = se_bo_config[depth]
        if depth > max_rounds:
            warnings.append(
                f"Bo por fase: rounds_from_final={depth} ignorado "
                f"(torneio terá {max_rounds} rodada(s))."
            )
        else:
            pruned[depth] = bo
    return (pruned if pruned else None), warnings
