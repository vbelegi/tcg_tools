"""Single elimination pairing."""

from __future__ import annotations

import random

from app.core.torneios.models import Pairing, PlayerRecord, TournamentState


class SingleEliminationStrategy:
    def generate_pairings(self, state: TournamentState, round_number: int) -> list[Pairing]:
        if round_number == 1:
            return self._round1(state)
        return self._advance_winners(state, round_number)

    def _round1(self, state: TournamentState) -> list[Pairing]:
        active = [p for p in state.players if not p.dropped_at]
        has_seeds = any(p.seed is not None for p in active)

        if has_seeds:
            ordered = sorted(active, key=lambda p: (p.seed or 9999, p.registration_order))
            pairings: list[Pairing] = []
            n = len(ordered)
            bracket_size = 1
            while bracket_size < n:
                bracket_size *= 2
            byes_needed = bracket_size - n
            bye_players = ordered[:byes_needed]
            rest = ordered[byes_needed:]
            for p in bye_players:
                pairings.append(Pairing(player1_id=p.id, player2_id=None, is_bye=True))
            for i in range(0, len(rest) - 1, 2):
                pairings.append(Pairing(player1_id=rest[i].id, player2_id=rest[i + 1].id))
            if len(rest) % 2 == 1:
                pairings.append(Pairing(player1_id=rest[-1].id, player2_id=None, is_bye=True))
            return pairings

        rng = random.Random(state.shuffle_seed)
        shuffled = active.copy()
        rng.shuffle(shuffled)
        pairings = []
        for i in range(0, len(shuffled) - 1, 2):
            pairings.append(Pairing(player1_id=shuffled[i].id, player2_id=shuffled[i + 1].id))
        if len(shuffled) % 2 == 1:
            pairings.append(Pairing(player1_id=shuffled[-1].id, player2_id=None, is_bye=True))
        return pairings

    def _advance_winners(self, state: TournamentState, round_number: int) -> list[Pairing]:
        prev_round = round_number - 1
        winners: list[PlayerRecord] = []
        for m in state.matches:
            if m.round_number != prev_round:
                continue
            if m.is_bye:
                winners.append(next(p for p in state.players if p.id == m.player1_id))
            elif m.winner_id:
                winners.append(next(p for p in state.players if p.id == m.winner_id))

        pairings: list[Pairing] = []
        for i in range(0, len(winners) - 1, 2):
            pairings.append(Pairing(player1_id=winners[i].id, player2_id=winners[i + 1].id))
        if len(winners) % 2 == 1:
            pairings.append(Pairing(player1_id=winners[-1].id, player2_id=None, is_bye=True))
        return pairings
