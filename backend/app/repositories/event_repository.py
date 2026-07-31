"""Event repository."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.core.torneios.models import MatchRecord, PlayerRecord, TournamentState
from app.models import Event, Match, Player, Round
from app.repositories.protocols import EventRepositoryProtocol


class EventRepository(EventRepositoryProtocol):
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        name: str,
        event_date: date,
        format: str,
        max_rounds: int | None,
        entry_fee: float,
        best_of: int,
        premiacao_preset: dict[str, Any],
        shuffle_seed: int,
    ) -> Event:
        event = Event(
            name=name,
            event_date=event_date,
            format=format,
            max_rounds=max_rounds,
            entry_fee=entry_fee,
            best_of=best_of,
            premiacao_preset=premiacao_preset,
            status="draft",
            shuffle_seed=shuffle_seed,
        )
        self._db.add(event)
        self._db.flush()
        return event

    def get(self, event_id: int) -> Event | None:
        return (
            self._db.query(Event)
            .options(
                joinedload(Event.players),
                joinedload(Event.rounds).joinedload(Round.matches),
            )
            .filter(Event.id == event_id)
            .first()
        )

    def list_all(self) -> list[Event]:
        return self._db.query(Event).order_by(Event.created_at.desc()).all()

    def add_player(self, event_id: int, name: str, seed: int | None, order: int) -> Player:
        player = Player(event_id=event_id, name=name, seed=seed, registration_order=order)
        self._db.add(player)
        self._db.flush()
        return player

    def remove_player(self, player: Player) -> None:
        self._db.delete(player)

    def to_tournament_state(self, event: Event) -> TournamentState:
        players = [
            PlayerRecord(
                id=p.id,
                name=p.name,
                seed=p.seed,
                registration_order=p.registration_order,
                dropped_at=p.dropped_at,
            )
            for p in sorted(event.players, key=lambda x: x.registration_order)
        ]
        matches: list[MatchRecord] = []
        played_pairs: set[frozenset[int]] = set()
        current_round = 0
        for rnd in sorted(event.rounds, key=lambda r: r.number):
            if rnd.status == "active":
                current_round = rnd.number
            for m in rnd.matches:
                matches.append(MatchRecord(
                    id=m.id,
                    round_number=rnd.number,
                    player1_id=m.player1_id,
                    player2_id=m.player2_id,
                    score_p1=m.score_p1,
                    score_p2=m.score_p2,
                    is_bye=m.is_bye,
                    is_walkover=m.is_walkover,
                    had_rematch=m.had_rematch,
                    scores_submitted=m.scores_submitted,
                    winner_id=m.winner_id,
                ))
                if m.player2_id and not m.is_bye:
                    played_pairs.add(frozenset({m.player1_id, m.player2_id}))

        if not current_round and event.rounds:
            active = [r for r in event.rounds if r.status == "active"]
            if active:
                current_round = active[0].number
            else:
                completed = [r for r in event.rounds if r.status == "completed"]
                current_round = max((r.number for r in completed), default=0)

        return TournamentState(
            event_id=event.id,
            format=event.format,
            best_of=event.best_of,
            max_rounds=event.max_rounds or 0,
            current_round=current_round,
            status=event.status,
            shuffle_seed=event.shuffle_seed or 0,
            players=players,
            matches=matches,
            played_pairs=played_pairs,
        )

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def refresh(self, obj: object) -> None:
        self._db.refresh(obj)
