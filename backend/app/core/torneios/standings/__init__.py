"""Standings and tiebreakers."""

from __future__ import annotations

import random

from app.core.torneios.models import MatchRecord, StandingRow, TournamentState
from app.core.torneios.standings.omw import game_win_pct
from app.core.torneios.standings.se import compute_se_standings
from app.core.torneios.standings.stats import build_player_stats
from app.core.torneios.standings.tiebreakers import ogw_for_player, omw_for_player


def compute_standings(state: TournamentState, decklists: dict[int, str | None] | None = None) -> list[StandingRow]:
    stats = build_player_stats(state)
    decklists = decklists or {}

    active_rows: list[tuple] = []
    dropped_ids: list[int] = []

    for pid, p in stats.items():
        if p.dropped_at:
            dropped_ids.append(pid)
            continue
        omw = omw_for_player(pid, stats, state.matches)
        gw = game_win_pct(p.game_wins, p.game_losses, p.game_draws)
        ogw = ogw_for_player(pid, stats, state.matches)
        active_rows.append((p.match_points, omw, gw, ogw, p.seed or 9999, p.registration_order, pid, p.name))

    active_rows.sort(key=lambda r: (-r[0], -r[1], -r[2], -r[3], r[4], r[5]))

    result: list[StandingRow] = []
    for i, (pts, omw, gw, ogw, _, _, pid, name) in enumerate(active_rows):
        result.append(
            StandingRow(
                rank=i + 1,
                player_id=pid,
                name=name,
                points=pts,
                omw=round(omw, 4),
                gw=round(gw, 4),
                ogw=round(ogw, 4),
                decklist=decklists.get(pid),
            )
        )

    if dropped_ids:
        rng = random.Random(state.shuffle_seed)
        rng.shuffle(dropped_ids)
        base_rank = len(result) + 1
        for j, pid in enumerate(dropped_ids):
            p = stats[pid]
            result.append(
                StandingRow(
                    rank=base_rank + j,
                    player_id=pid,
                    name=p.name,
                    points=p.match_points,
                    omw=0.0,
                    gw=0.0,
                    ogw=0.0,
                    decklist=decklists.get(pid),
                    is_drop=True,
                    rank_label="DROP",
                )
            )

    return result


def compute_match_records(
    state: TournamentState,
    *,
    before_round: int | None = None,
) -> dict[int, dict[str, int]]:
    """W/L/D por jogador; ``before_round`` limita a rodadas anteriores (record ao entrar na rodada)."""
    matches = (
        state.matches
        if before_round is None
        else [m for m in state.matches if m.round_number < before_round]
    )
    partial = TournamentState(
        event_id=state.event_id,
        format=state.format,
        best_of=state.best_of,
        max_rounds=state.max_rounds,
        current_round=state.current_round,
        status=state.status,
        shuffle_seed=state.shuffle_seed,
        players=state.players,
        matches=matches,
        played_pairs=state.played_pairs,
        third_place_match=state.third_place_match,
        se_bo_config=state.se_bo_config,
    )
    stats = build_player_stats(partial)
    return {
        pid: {"wins": p.wins, "losses": p.losses, "draws": p.draws}
        for pid, p in stats.items()
    }


__all__ = ["compute_standings", "compute_se_standings", "compute_match_records"]
