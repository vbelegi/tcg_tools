"""OMW% with fictional BYE opponent."""

from __future__ import annotations


def match_win_pct(wins: int, losses: int, draws: int) -> float:
    played = wins + losses + draws
    if played == 0:
        return 0.33
    return (wins + 0.5 * draws) / played


def oponente_bye_ficticio(record_pre_bye: tuple[int, int, int]) -> float:
    """BYE opponent mirrors player's record before bye round."""
    wins, losses, draws = record_pre_bye
    return match_win_pct(wins, losses, draws)


def game_win_pct(gw: int, gl: int, gd: int) -> float:
    total = gw + gl + gd
    if total == 0:
        return 0.33
    return (gw + 0.5 * gd) / total
