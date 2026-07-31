"""Torneio API schemas."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TorneioCreateRequest(BaseModel):
    name: str
    event_date: date
    format: str
    max_rounds: int | None = None
    entry_fee: float = 0
    best_of: int = Field(default=3, ge=1, le=5)
    premiacao_preset_id: str = "standard"
    third_place_match: bool = False
    se_bo_config: dict[str, int] | None = None

    @field_validator("se_bo_config")
    @classmethod
    def validate_se_bo_config(cls, v: dict[str, int] | None) -> dict[str, int] | None:
        if v is None:
            return None
        for key, val in v.items():
            if int(key) < 1:
                raise ValueError("se_bo_config keys must be positive rounds_from_final.")
            if val not in (1, 3, 5):
                raise ValueError("se_bo_config values must be 1, 3, or 5.")
        return v


class TorneioUpdate(BaseModel):
    name: str | None = None
    event_date: date | None = None
    entry_fee: float | None = None
    best_of: int | None = Field(default=None, ge=1, le=5)
    max_rounds: int | None = None
    third_place_match: bool | None = None
    se_bo_config: dict[str, int] | None = None

    @field_validator("se_bo_config")
    @classmethod
    def validate_se_bo_config(cls, v: dict[str, int] | None) -> dict[str, int] | None:
        if v is None:
            return None
        for key, val in v.items():
            if int(key) < 1:
                raise ValueError("se_bo_config keys must be positive rounds_from_final.")
            if val not in (1, 3, 5):
                raise ValueError("se_bo_config values must be 1, 3, or 5.")
        return v


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
