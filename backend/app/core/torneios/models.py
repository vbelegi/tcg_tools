"""Torneio domain models (pure dataclasses)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PlayerRecord:
    id: int
    name: str
    seed: int | None
    registration_order: int
    dropped_at: datetime | None = None
    wins: int = 0
    losses: int = 0
    draws: int = 0
    match_points: int = 0
    game_wins: int = 0
    game_losses: int = 0
    game_draws: int = 0
    opponents: list[int] = field(default_factory=list)
    bye_rounds: list[tuple[int, tuple[int, int, int]]] = field(default_factory=list)


@dataclass
class MatchRecord:
    id: int
    round_number: int
    player1_id: int
    player2_id: int | None
    score_p1: int
    score_p2: int
    is_bye: bool
    is_walkover: bool
    had_rematch: bool
    scores_submitted: bool
    winner_id: int | None


@dataclass
class Pairing:
    player1_id: int
    player2_id: int | None
    is_bye: bool = False
    had_rematch: bool = False


@dataclass
class TournamentState:
    event_id: int
    format: str
    best_of: int
    max_rounds: int
    current_round: int
    status: str
    shuffle_seed: int
    players: list[PlayerRecord]
    matches: list[MatchRecord]
    played_pairs: set[frozenset[int]] = field(default_factory=set)


@dataclass
class StandingRow:
    rank: int
    player_id: int
    name: str
    points: int
    omw: float
    gw: float
    ogw: float
    decklist: str | None = None
    is_drop: bool = False
    rank_label: str | None = None
