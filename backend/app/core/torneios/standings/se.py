"""Single elimination standings by placement bands."""

from __future__ import annotations

import random

from app.core.torneios.models import StandingRow, TournamentState
from app.core.torneios.standings.omw import game_win_pct
from app.core.torneios.standings.se_bracket import (
    band_label_for_elimination_round,
    bronze_match,
    final_match,
    losers_in_round,
    match_loser,
    semi_losers,
)
from app.core.torneios.se_bands import format_band_label
from app.core.torneios.standings.stats import build_player_stats
from app.core.torneios.standings.tiebreakers import ogw_for_player, omw_for_player


def compute_se_standings(
    state: TournamentState,
    decklists: dict[int, str | None] | None = None,
) -> list[StandingRow]:
    decklists = decklists or {}
    stats = build_player_stats(state)
    max_rounds = state.max_rounds or 1
    assignments: dict[int, str] = {}
    assigned: set[int] = set()

    def assign(pid: int, label: str) -> None:
        if pid in assigned:
            return
        assignments[pid] = label
        assigned.add(pid)

    fm = final_match(state, max_rounds)
    if fm and fm.winner_id:
        assign(fm.winner_id, "1º")
        loser = match_loser(fm)
        if loser:
            assign(loser, "2º")

    if state.third_place_match:
        bm = bronze_match(state, max_rounds)
        if bm and bm.winner_id:
            assign(bm.winner_id, "3º")
            bl = match_loser(bm)
            if bl:
                assign(bl, "4º")
        else:
            semi = semi_losers(state, max_rounds)
            if len(semi) == 1:
                assign(semi[0], "3º")
    else:
        for pid in semi_losers(state, max_rounds):
            assign(pid, format_band_label(3, 4))

    for rnd in range(1, max_rounds):
        if rnd == max_rounds - 1 and not state.third_place_match:
            continue
        if rnd == max_rounds - 1 and state.third_place_match:
            continue
        label = band_label_for_elimination_round(rnd, max_rounds, state.third_place_match)
        for pid in losers_in_round(state, rnd):
            assign(pid, label)

    active_rows: list[tuple] = []
    for pid, label in assignments.items():
        p = stats[pid]
        omw = omw_for_player(pid, stats, state.matches)
        gw = game_win_pct(p.game_wins, p.game_losses, p.game_draws)
        ogw = ogw_for_player(pid, stats, state.matches)
        active_rows.append(
            (label, p.match_points, omw, gw, ogw, p.seed or 9999, p.registration_order, pid, p.name)
        )

    def _label_sort_key(label: str) -> tuple:
        if label == "DROP":
            return (999, 0, 0)
        if label.endswith("º") and "–" not in label:
            return (int(label.replace("º", "")), 0, 0)
        if "–" in label:
            lo, hi = label.replace("º", "").split("–")
            return (int(lo), 0, 1)
        return (999, 0, 2)

    active_rows.sort(
        key=lambda r: (
            _label_sort_key(r[0]),
            -r[1],
            -r[2],
            -r[3],
            -r[4],
            r[5],
            r[6],
        )
    )

    result: list[StandingRow] = []
    for i, (_, pts, omw, gw, ogw, _, _, pid, name) in enumerate(active_rows):
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
                rank_label=assignments[pid],
            )
        )

    dropped_ids = [p.id for p in state.players if p.dropped_at and p.id not in assigned]
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

    unassigned = [
        p.id for p in state.players if not p.dropped_at and p.id not in assigned
    ]
    for pid in unassigned:
        p = stats[pid]
        result.append(
            StandingRow(
                rank=len(result) + 1,
                player_id=pid,
                name=p.name,
                points=p.match_points,
                omw=0.0,
                gw=0.0,
                ogw=0.0,
                decklist=decklists.get(pid),
                rank_label="—",
            )
        )

    return result
