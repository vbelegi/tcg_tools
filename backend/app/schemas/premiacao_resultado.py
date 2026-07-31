"""Persisted premiação resultado schema (torneio finalize snapshot)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PremiacaoBandSnapshot(BaseModel):
    label: str
    pool: float
    tier_indices: list[int]
    player_count: int
    payout_per_player: float | None = None


class PlayerPayoutSnapshot(BaseModel):
    player_id: int
    name: str
    band_label: str
    payout: float


class PremiacaoResultado(BaseModel):
    """Standard shape stored in `events.premiacao_resultado`."""

    schema_version: Literal[1, 2] = 1
    jogadores: int = Field(ge=1)
    premiados: int = Field(ge=1)
    premios: list[float]
    entry_fee: float = Field(ge=0)
    creditos: list[float] | None = None
    total_creditos: float | None = None
    standings_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    bands: list[PremiacaoBandSnapshot] | None = None
    player_payouts: list[PlayerPayoutSnapshot] | None = None

    @field_validator("premios")
    @classmethod
    def premios_non_negative(cls, v: list[float]) -> list[float]:
        if any(p < 0 for p in v):
            raise ValueError("premios must be non-negative.")
        return v

    @model_validator(mode="after")
    def creditos_match_player_payouts(self) -> PremiacaoResultado:
        if self.creditos is not None and self.player_payouts is not None:
            if len(self.creditos) != len(self.player_payouts):
                raise ValueError("creditos length must match player_payouts when both present.")
        return self

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PremiacaoResultado:
        return cls.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=False)


def validate_premiacao_resultado(data: dict[str, Any]) -> PremiacaoResultado:
    """Validate persisted premiação; raises ValidationError on mismatch."""
    return PremiacaoResultado.from_dict(data)
