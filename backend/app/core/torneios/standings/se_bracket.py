"""Pure bracket queries for single elimination."""

from __future__ import annotations

from app.core.torneios.models import MatchRecord, PlayerRecord, TournamentState
from app.core.torneios.se_bands import format_band_label


def _matches_in_round(state: TournamentState, round_number: int) -> list[MatchRecord]:
    return [m for m in state.matches if m.round_number == round_number]


def main_bracket_matches(state: TournamentState, round_number: int) -> list[MatchRecord]:
    return [m for m in _matches_in_round(state, round_number) if not m.is_third_place]


def final_match(state: TournamentState, max_rounds: int) -> MatchRecord | None:
    finals = [m for m in main_bracket_matches(state, max_rounds) if not m.is_bye]
    return finals[0] if finals else None


def bronze_match(state: TournamentState, max_rounds: int) -> MatchRecord | None:
    bronze = [m for m in _matches_in_round(state, max_rounds) if m.is_third_place]
    return bronze[0] if bronze else None


def match_loser(match: MatchRecord) -> int | None:
    if match.is_bye or match.winner_id is None:
        return None
    if match.winner_id == match.player1_id:
        return match.player2_id
    return match.player1_id


def _player_active(players: dict[int, PlayerRecord], pid: int | None) -> bool:
    if pid is None:
        return False
    p = players.get(pid)
    return p is not None and p.dropped_at is None


def semi_losers(state: TournamentState, max_rounds: int) -> list[int]:
    if max_rounds < 2:
        return []
    semi_round = max_rounds - 1
    losers: list[int] = []
    players = {p.id: p for p in state.players}
    for m in main_bracket_matches(state, semi_round):
        if m.is_bye:
            continue
        loser = match_loser(m)
        if loser and _player_active(players, loser):
            losers.append(loser)
    return losers


def band_label_for_elimination_round(
    round_number: int,
    max_rounds: int,
    third_place_match: bool,
) -> str:
    if round_number == max_rounds:
        return "2º"
    if round_number == max_rounds - 1 and not third_place_match:
        return format_band_label(3, 4)
    depth = max_rounds - round_number
    lo = 2**depth + 1
    hi = 2 ** (depth + 1)
    return format_band_label(lo, hi)


def losers_in_round(state: TournamentState, round_number: int) -> list[int]:
    players = {p.id: p for p in state.players}
    losers: list[int] = []
    for m in main_bracket_matches(state, round_number):
        if m.is_bye:
            continue
        loser = match_loser(m)
        if loser and _player_active(players, loser):
            losers.append(loser)
    return losers
