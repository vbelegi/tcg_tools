"""Torneios API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.torneio import (
    ClassificacaoPatch,
    DropRequest,
    JogadorCreate,
    MatchUpdate,
    TorneioCreateRequest,
    TorneioUpdate,
)
from app.services.torneio_service import TorneioError, TorneioService

router = APIRouter(prefix="/torneios", tags=["torneios"])


def get_torneio_service(db: Session = Depends(get_db)) -> TorneioService:
    return TorneioService(db)


@router.post("")
def create_torneio(body: TorneioCreateRequest, svc: TorneioService = Depends(get_torneio_service)):
    try:
        event = svc.create_event(
            body.name,
            body.event_date,
            body.format,
            body.max_rounds,
            body.entry_fee,
            body.best_of,
            body.premiacao_preset_id,
        )
        return svc.get_event(event.id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("")
def list_torneios(svc: TorneioService = Depends(get_torneio_service)):
    return svc.list_events()


@router.get("/{event_id}")
def get_torneio(event_id: int, svc: TorneioService = Depends(get_torneio_service)):
    try:
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{event_id}")
def update_torneio(
    event_id: int,
    body: TorneioUpdate,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.update_event(event_id, body.model_dump(exclude_unset=True))
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/jogadores")
def add_jogador(
    event_id: int,
    body: JogadorCreate,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        player = svc.add_player(event_id, body.name, body.seed)
        return {
            "id": player.id,
            "name": player.name,
            "seed": player.seed,
            "registration_order": player.registration_order,
            "dropped_at": None,
            "decklist": None,
        }
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{event_id}/jogadores/{player_id}", status_code=204)
def remove_jogador(
    event_id: int,
    player_id: int,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.remove_player(event_id, player_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/iniciar")
def iniciar(event_id: int, svc: TorneioService = Depends(get_torneio_service)):
    try:
        svc.start_event(event_id)
        return svc.get_event(event_id)
    except (TorneioError, Exception) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{event_id}/rodadas")
def list_rodadas(event_id: int, svc: TorneioService = Depends(get_torneio_service)):
    try:
        return svc.get_rounds(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{event_id}/rodadas/{number}")
def get_rodada(event_id: int, number: int, svc: TorneioService = Depends(get_torneio_service)):
    try:
        return svc.get_round(event_id, number)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{event_id}/matches/{match_id}")
def update_match(
    event_id: int,
    match_id: int,
    body: MatchUpdate,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.update_match(event_id, match_id, body.score_p1, body.score_p2)
        return {"ok": True}
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/jogadores/{player_id}/drop", status_code=204)
def drop_jogador(
    event_id: int,
    player_id: int,
    body: DropRequest,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.drop_player(event_id, player_id, body.mid_round)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/avancar")
def avancar(event_id: int, svc: TorneioService = Depends(get_torneio_service)):
    """Conclui a rodada ativa (sem iniciar a próxima)."""
    try:
        svc.complete_round(event_id)
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/iniciar-proxima-rodada")
def iniciar_proxima_rodada(event_id: int, svc: TorneioService = Depends(get_torneio_service)):
    try:
        svc.start_next_round(event_id)
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/rodadas/reabrir")
def reabrir_rodada(
    event_id: int,
    number: int | None = None,
    svc: TorneioService = Depends(get_torneio_service),
):
    """Reabre a última rodada concluída (ou a anterior à rodada ativa) para correções."""
    try:
        svc.reopen_round(event_id, round_number=number)
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/finalizar")
def finalizar(event_id: int, svc: TorneioService = Depends(get_torneio_service)):
    try:
        svc.finalize(event_id)
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{event_id}/premiacao")
def get_premiacao(event_id: int, svc: TorneioService = Depends(get_torneio_service)):
    try:
        return svc.get_premiacao(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{event_id}/classificacao")
def get_classificacao(event_id: int, svc: TorneioService = Depends(get_torneio_service)):
    try:
        return {"standings": svc.get_classificacao(event_id)}
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{event_id}/classificacao", status_code=204)
def patch_classificacao(
    event_id: int,
    body: ClassificacaoPatch,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.update_decklists(event_id, [u.model_dump() for u in body.updates])
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/export-log")
def export_log(event_id: int, svc: TorneioService = Depends(get_torneio_service)):
    try:
        content, filename = svc.export_log(event_id)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
