"""Pairing strategy protocol."""

from __future__ import annotations

from typing import Protocol

from app.core.torneios.models import Pairing, TournamentState


class PairingStrategy(Protocol):
    def generate_pairings(self, state: TournamentState, round_number: int) -> list[Pairing]: ...
