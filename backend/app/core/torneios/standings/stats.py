"""Player statistics for standings tiebreakers."""

from __future__ import annotations

from app.core.torneios.models import MatchRecord, PlayerRecord, TournamentState


def build_player_stats(state: TournamentState) -> dict[int, PlayerRecord]:
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
