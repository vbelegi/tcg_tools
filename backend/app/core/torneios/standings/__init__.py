"""Standings and tiebreakers."""

from __future__ import annotations

import random

from app.core.torneios.models import MatchRecord, PlayerRecord, StandingRow, TournamentState
from app.core.torneios.standings.omw import game_win_pct, match_win_pct, oponente_bye_ficticio


def _bye_pre_record(pid: int, matches: list[MatchRecord], round_number: int) -> tuple[int, int, int]:
    pre_w = sum(
        1
        for x in matches
        if x.round_number < round_number
        and ((x.player1_id == pid and x.winner_id == pid) or (x.player2_id == pid and x.winner_id == pid))
    )
    pre_l = sum(
        1
        for x in matches
        if x.round_number < round_number
        and (
            (x.player1_id == pid and x.winner_id and x.winner_id != pid)
            or (x.player2_id == pid and x.winner_id and x.winner_id != pid)
        )
    )
    pre_d = sum(
        1
        for x in matches
        if x.round_number < round_number
        and (x.player1_id == pid or x.player2_id == pid)
        and x.winner_id is None
        and x.score_p1 == x.score_p2
    )
    return pre_w, pre_l, pre_d


def _build_player_stats(state: TournamentState) -> dict[int, PlayerRecord]:
    players = {
        p.id: PlayerRecord(
            id=p.id,
            name=p.name,
            seed=p.seed,
            registration_order=p.registration_order,
            dropped_at=p.dropped_at,
        )
        for p in state.players
    }

    for m in state.matches:
        p1 = players[m.player1_id]
        if m.is_bye:
            p1.wins += 1
            p1.match_points += 3
            gw = (state.best_of + 1) // 2
            p1.game_wins += gw
            continue
        if m.player2_id is None:
            continue
        p2 = players[m.player2_id]
        p1.opponents.append(p2.id)
        p2.opponents.append(p1.id)

        if m.winner_id is None and m.score_p1 == m.score_p2:
            p1.draws += 1
            p2.draws += 1
            p1.match_points += 1
            p2.match_points += 1
            p1.game_draws += m.score_p1
            p2.game_draws += m.score_p2
            p1.game_wins += m.score_p1
            p2.game_wins += m.score_p2
        elif m.winner_id == p1.id:
            p1.wins += 1
            p2.losses += 1
            p1.match_points += 3
            p1.game_wins += m.score_p1
            p1.game_losses += m.score_p2
            p2.game_wins += m.score_p2
            p2.game_losses += m.score_p1
        elif m.winner_id == p2.id:
            p2.wins += 1
            p1.losses += 1
            p2.match_points += 3
            p2.game_wins += m.score_p2
            p2.game_losses += m.score_p1
            p1.game_wins += m.score_p1
            p1.game_losses += m.score_p2

    return players


def _omw_for_player(pid: int, stats: dict[int, PlayerRecord], matches: list[MatchRecord]) -> float:
    player = stats[pid]
    if not player.opponents and not any(m.is_bye and m.player1_id == pid for m in matches):
        return 0.33

    omw_values: list[float] = []
    for oid in player.opponents:
        opp = stats[oid]
        omw_values.append(match_win_pct(opp.wins, opp.losses, opp.draws))

    for m in matches:
        if m.is_bye and m.player1_id == pid:
            omw_values.append(oponente_bye_ficticio(_bye_pre_record(pid, matches, m.round_number)))

    if not omw_values:
        return 0.33
    return sum(omw_values) / len(omw_values)


def _ogw_for_player(pid: int, stats: dict[int, PlayerRecord], matches: list[MatchRecord]) -> float:
    player = stats[pid]
    ogw_values: list[float] = []
    for oid in player.opponents:
        o = stats[oid]
        ogw_values.append(game_win_pct(o.game_wins, o.game_losses, o.game_draws))

    for m in matches:
        if m.is_bye and m.player1_id == pid:
            pre = _bye_pre_record(pid, matches, m.round_number)
            w, l, d = pre
            played = w + l + d
            if played == 0:
                ogw_values.append(0.33)
            else:
                ogw_values.append(oponente_bye_ficticio(pre))

    if not ogw_values:
        return 0.33
    return sum(ogw_values) / len(ogw_values)


def compute_standings(state: TournamentState, decklists: dict[int, str | None] | None = None) -> list[StandingRow]:
    stats = _build_player_stats(state)
    decklists = decklists or {}

    active_rows: list[tuple] = []
    dropped_ids: list[int] = []

    for pid, p in stats.items():
        if p.dropped_at:
            dropped_ids.append(pid)
            continue
        omw = _omw_for_player(pid, stats, state.matches)
        gw = game_win_pct(p.game_wins, p.game_losses, p.game_draws)
        ogw = _ogw_for_player(pid, stats, state.matches)
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
    )
    stats = _build_player_stats(partial)
    return {
        pid: {"wins": p.wins, "losses": p.losses, "draws": p.draws}
        for pid, p in stats.items()
    }

