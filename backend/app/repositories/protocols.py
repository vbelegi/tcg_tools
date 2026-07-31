"""Repository protocols for dependency injection and testing."""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol

from app.core.torneios.models import TournamentState
from app.models import Event, Player


class EventRepositoryProtocol(Protocol):
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
        third_place_match: bool = False,
        se_bo_config: dict[str, Any] | None = None,
    ) -> Event: ...

    def get(self, event_id: int) -> Event | None: ...

    def list_all(self) -> list[Event]: ...

    def add_player(self, event_id: int, name: str, seed: int | None, order: int) -> Player: ...

    def remove_player(self, player: Player) -> None: ...

    def to_tournament_state(self, event: Event) -> TournamentState: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def refresh(self, obj: object) -> None: ...
