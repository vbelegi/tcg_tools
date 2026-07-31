"""Premiação API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import Response

from app.core.premiacao.validation import ConfigError, InputError
from app.schemas.premiacao import (
    CalcularRequest,
    CalcularResponse,
    ExportRequest,
    PresetBody,
    PresetsResponse,
    TabelaLinha,
    TabelaResponse,
)
from app.services.premiacao_service import PremiacaoService

router = APIRouter(prefix="/premiacao", tags=["premiacao"])


def get_premiacao_service() -> PremiacaoService:
    return PremiacaoService()


@router.get("/presets", response_model=PresetsResponse)
def list_presets(svc: PremiacaoService = Depends(get_premiacao_service)) -> PresetsResponse:
    store = svc.list_presets()
    presets = {k: PresetBody(**v) for k, v in store["presets"].items()}
    return PresetsResponse(
        default_preset=store["default_preset"],
        presets=presets,
        exports_desatualizados=svc.exports_desatualizados(),
        presets_updated_at=svc.presets_mtime(),
    )


@router.get("/presets/{preset_id}", response_model=PresetBody)
def get_preset(
    preset_id: str,
    svc: PremiacaoService = Depends(get_premiacao_service),
) -> PresetBody:
    try:
        return PresetBody(**svc.get_preset(preset_id))
    except ConfigError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/presets/{preset_id}", response_model=PresetBody)
def update_preset(
    preset_id: str,
    body: PresetBody,
    svc: PremiacaoService = Depends(get_premiacao_service),
    x_presets_mtime: float | None = Header(default=None, alias="X-Presets-Mtime"),
) -> PresetBody:
    try:
        updated = svc.update_preset(preset_id, body.model_dump(), x_presets_mtime)
        return PresetBody(**updated)
    except ConfigError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/calcular", response_model=CalcularResponse)
def calcular_endpoint(
    body: CalcularRequest,
    svc: PremiacaoService = Depends(get_premiacao_service),
) -> CalcularResponse:
    try:
        result = svc.calcular_torneio(
            body.jogadores,
            body.preset_id,
            body.valor_inscricao,
        )
        return CalcularResponse(**result)
    except (InputError, ConfigError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/tabela", response_model=TabelaResponse)
def tabela(
    ate: int = Query(..., ge=1),
    preset_id: str | None = None,
    svc: PremiacaoService = Depends(get_premiacao_service),
) -> TabelaResponse:
    try:
        linhas = svc.gerar_tabela(ate, preset_id)
        return TabelaResponse(linhas=[TabelaLinha(**l) for l in linhas])
    except (InputError, ConfigError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/export")
def export_csv(
    body: ExportRequest,
    svc: PremiacaoService = Depends(get_premiacao_service),
) -> Response:
    try:
        content, filename = svc.export_csv_bytes(body.ate, body.preset_id)
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except (InputError, ConfigError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
