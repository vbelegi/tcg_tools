"""Torneio API schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class TorneioCreateRequest(BaseModel):
    name: str
    event_date: date
    format: str
    max_rounds: int | None = None
    entry_fee: float = 0
    best_of: int = Field(default=3, ge=1, le=5)
    premiacao_preset_id: str = "standard"


class TorneioUpdate(BaseModel):
    name: str | None = None
    event_date: date | None = None
    entry_fee: float | None = None
    best_of: int | None = None
    max_rounds: int | None = None


class JogadorCreate(BaseModel):
    name: str
    seed: int | None = None


class MatchUpdate(BaseModel):
    score_p1: int
    score_p2: int


class DropRequest(BaseModel):
    mid_round: bool = False


class DecklistUpdate(BaseModel):
    player_id: int
    decklist: str | None = None


class ClassificacaoPatch(BaseModel):
    updates: list[DecklistUpdate]
