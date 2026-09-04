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
    registration_open: bool = True
    description: str | None = None
    start_time: str | None = None
    tcg_game_id: int
    pairing_mode: Literal["platform", "manual"] = "platform"

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

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        value = v.strip()
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("Horário deve ser HH:MM.")
        try:
            h, m = int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise ValueError("Horário deve ser HH:MM.") from exc
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("Horário inválido.")
        return f"{h:02d}:{m:02d}"


class TorneioUpdate(BaseModel):
    name: str | None = None
    event_date: date | None = None
    entry_fee: float | None = None
    best_of: int | None = Field(default=None, ge=1, le=5)
    max_rounds: int | None = None
    third_place_match: bool | None = None
    se_bo_config: dict[str, int] | None = None
    registration_open: bool | None = None
    description: str | None = None
    start_time: str | None = None
    tcg_game_id: int | None = None
    pairing_mode: Literal["platform", "manual"] | None = None

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

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        value = v.strip()
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("Horário deve ser HH:MM.")
        try:
            h, m = int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise ValueError("Horário deve ser HH:MM.") from exc
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("Horário inválido.")
        return f"{h:02d}:{m:02d}"


class ManualPlacement(BaseModel):
    player_id: int
    placement: int = Field(ge=1)
    is_drop: bool = False
    decklist: str | None = None


class ManualFinalizeRequest(BaseModel):
    placements: list[ManualPlacement]


class JogadorCreate(BaseModel):
    name: str
    seed: int | None = None
    user_id: int | None = None
    email: str | None = None
    phone: str | None = None
    create_account: bool = False
    attendance: Literal["pending", "checked_in"] = "checked_in"


class MatchUpdate(BaseModel):
    score_p1: int
    score_p2: int


class DropRequest(BaseModel):
    mid_round: bool = False


class DecklistUpdate(BaseModel):
    player_id: int
    decklist: str | None = None
    decklist_source: str | None = None
    decklist_source_id: str | None = None
    decklist_source_url: str | None = None
    decklist_name: str | None = None
    decklist_format: str | None = None
    decklist_price_low_brl: float | None = None
    decklist_imported_at: str | None = None  # ISO; server may overwrite


class ClassificacaoPatch(BaseModel):
    updates: list[DecklistUpdate]


class ExternalPlacement(BaseModel):
    placement: int = Field(ge=1)
    display_name: str
    user_id: int | None = None
    email: str | None = None
    phone: str | None = None
    create_account: bool = False
    decklist: str | None = None
    is_drop: bool = False


class ExternalTorneioCreate(BaseModel):
    name: str
    event_date: date
    format: str = "swiss"
    premiacao_preset_id: str = "standard"
    entry_fee: float = 0
    notes: str | None = None
    tcg_game_id: int
    placements: list[ExternalPlacement]
