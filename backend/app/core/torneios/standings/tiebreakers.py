"""Tiebreaker calculations for standings."""

from __future__ import annotations

from app.core.torneios.models import MatchRecord, PlayerRecord
from app.core.torneios.standings.omw import game_win_pct, match_win_pct, oponente_bye_ficticio


def bye_pre_record(pid: int, matches: list[MatchRecord], round_number: int) -> tuple[int, int, int]:
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


def omw_for_player(pid: int, stats: dict[int, PlayerRecord], matches: list[MatchRecord]) -> float:
    player = stats[pid]
    if not player.opponents and not any(m.is_bye and m.player1_id == pid for m in matches):
        return 0.33

    omw_values: list[float] = []
    for oid in player.opponents:
        opp = stats[oid]
        omw_values.append(match_win_pct(opp.wins, opp.losses, opp.draws))

    for m in matches:
        if m.is_bye and m.player1_id == pid:
            omw_values.append(oponente_bye_ficticio(bye_pre_record(pid, matches, m.round_number)))

    if not omw_values:
        return 0.33
    return sum(omw_values) / len(omw_values)


def ogw_for_player(pid: int, stats: dict[int, PlayerRecord], matches: list[MatchRecord]) -> float:
    player = stats[pid]
    ogw_values: list[float] = []
    for oid in player.opponents:
        o = stats[oid]
        ogw_values.append(game_win_pct(o.game_wins, o.game_losses, o.game_draws))

    for m in matches:
        if m.is_bye and m.player1_id == pid:
            pre = bye_pre_record(pid, matches, m.round_number)
            w, l, d = pre
            played = w + l + d
            if played == 0:
                ogw_values.append(0.33)
            else:
                ogw_values.append(oponente_bye_ficticio(pre))

    if not ogw_values:
        return 0.33
    return sum(ogw_values) / len(ogw_values)
