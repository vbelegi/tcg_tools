"""Swiss pairing strategy."""

from __future__ import annotations

import random

from app.core.torneios.models import Pairing, StandingRow, TournamentState
from app.core.torneios.standings import compute_standings

# Penalidade por cruzar brackets de pontuação (uppair/downpair).
_POINT_BRACKET_PENALTY = 100
# Rematch só entra quando não há pareamento perfeito sem repetição.
_REMATCH_BASE_COST = 10_000


class SwissPairingStrategy:
    def generate_pairings(self, state: TournamentState, round_number: int) -> list[Pairing]:
        active = [p for p in state.players if not p.dropped_at]
        if round_number == 1:
            return self._round1(state, active)
        return self._swiss_round(state, active, round_number)

    def _round1(self, state: TournamentState, active: list) -> list[Pairing]:
        has_seeds = any(p.seed is not None for p in active)
        if has_seeds:
            ordered = sorted(active, key=lambda p: (p.seed or 9999, p.registration_order))
            pairings = []
            n = len(ordered)
            for i in range(n // 2):
                pairings.append(Pairing(player1_id=ordered[i].id, player2_id=ordered[n - 1 - i].id))
            if n % 2 == 1:
                mid = ordered[n // 2]
                pairings.append(Pairing(player1_id=mid.id, player2_id=None, is_bye=True))
            return pairings

        rng = random.Random(state.shuffle_seed + 1)
        shuffled = active.copy()
        rng.shuffle(shuffled)
        pairings = []
        for i in range(0, len(shuffled) - 1, 2):
            pairings.append(Pairing(player1_id=shuffled[i].id, player2_id=shuffled[i + 1].id))
        if len(shuffled) % 2 == 1:
            pairings.append(Pairing(player1_id=shuffled[-1].id, player2_id=None, is_bye=True))
        return pairings

    def _swiss_round(self, state: TournamentState, active: list, round_number: int) -> list[Pairing]:
        standings = compute_standings(state)
        rank_map = {s.player_id: s.rank for s in standings}
        sorted_players = sorted(active, key=lambda p: rank_map.get(p.id, 999))

        if len(sorted_players) % 2 == 1:
            bye_player = self._pick_bye_player(state, sorted_players, round_number)
            sorted_players = [p for p in sorted_players if p.id != bye_player.id]
            bye_pairing = Pairing(player1_id=bye_player.id, player2_id=None, is_bye=True)
        else:
            bye_pairing = None

        pairings = self._pair_with_updown(state, sorted_players, standings)
        if bye_pairing:
            pairings.append(bye_pairing)
        return pairings

    def _pick_bye_player(self, state: TournamentState, sorted_players: list, round_number: int):
        prev_round = round_number - 1
        prev_winners = set()
        for m in state.matches:
            if m.round_number == prev_round and m.winner_id:
                prev_winners.add(m.winner_id)
            if m.round_number == prev_round and m.is_bye:
                prev_winners.add(m.player1_id)

        for p in reversed(sorted_players):
            if p.id not in prev_winners:
                return p
        return sorted_players[-1]

    def _pair_with_updown(
        self,
        state: TournamentState,
        sorted_players: list,
        standings: list[StandingRow],
    ) -> list[Pairing]:
        """Pair by rank with uppair/downpair before allowing rematches."""
        matched = self._find_optimal_matching(state, sorted_players, standings, allow_rematch=False)
        if matched is None:
            matched = self._find_optimal_matching(state, sorted_players, standings, allow_rematch=True)
        if matched is None:
            raise RuntimeError("Não foi possível parear jogadores ativos.")

        return [
            Pairing(player1_id=p1, player2_id=p2, had_rematch=rematch)
            for p1, p2, rematch in matched
        ]

    def _find_optimal_matching(
        self,
        state: TournamentState,
        sorted_players: list,
        standings: list[StandingRow],
        *,
        allow_rematch: bool,
    ) -> list[tuple[int, int, bool]] | None:
        pts_map = {s.player_id: s.points for s in standings}
        rank_map = {s.player_id: s.rank for s in standings}
        player_ids = [p.id for p in sorted_players]

        best: list[tuple[int, int, bool]] | None = None
        best_cost = float("inf")

        def pair_cost(a: int, b: int, rematch: bool) -> int:
            rank_diff = abs(rank_map.get(a, 999) - rank_map.get(b, 999))
            if rematch:
                return _REMATCH_BASE_COST + rank_diff
            pt_diff = abs(pts_map.get(a, 0) - pts_map.get(b, 0))
            return pt_diff * _POINT_BRACKET_PENALTY + rank_diff

        def search(
            remaining: list[int],
            pairs: list[tuple[int, int, bool]],
            cost: int,
        ) -> None:
            nonlocal best, best_cost
            if cost >= best_cost:
                return
            if not remaining:
                if cost < best_cost:
                    best = pairs.copy()
                    best_cost = cost
                return

            p1 = remaining[0]
            rest = remaining[1:]
            for i, p2 in enumerate(rest):
                pair_key = frozenset({p1, p2})
                rematch = pair_key in state.played_pairs
                if rematch and not allow_rematch:
                    continue
                new_rest = rest[:i] + rest[i + 1:]
                pairs.append((p1, p2, rematch))
                search(new_rest, pairs, cost + pair_cost(p1, p2, rematch))
                pairs.pop()

        search(player_ids, [], 0)
        return best
