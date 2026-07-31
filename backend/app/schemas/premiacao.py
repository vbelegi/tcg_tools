"""Premiação API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PresetBody(BaseModel):
    label: str
    min_jogadores: int
    min_premiados: int
    max_premiados: int
    crescimento: int
    r: float
    casas_decimais: int


class PresetsResponse(BaseModel):
    default_preset: str
    presets: dict[str, PresetBody]
    exports_desatualizados: bool = False
    presets_updated_at: float | None = None


class PresetUpdateRequest(BaseModel):
    preset: PresetBody
    expected_mtime: float | None = None
    presets_updated_at: float | None = None


class CalcularRequest(BaseModel):
    jogadores: int = Field(ge=1)
    preset_id: str | None = None
    valor_inscricao: float | None = None


class CalcularResponse(BaseModel):
    jogadores: int
    premiados: int
    premios: list[float]
    total_inscricoes: float
    creditos: list[float] | None = None


class TabelaLinha(BaseModel):
    jogadores: int
    premiados: int
    premios: list[float]


class TabelaResponse(BaseModel):
    linhas: list[TabelaLinha]


class ExportRequest(BaseModel):
    ate: int = Field(ge=1)
    preset_id: str | None = None
