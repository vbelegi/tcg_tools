"""Torneios API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireStaff, get_current_user, get_optional_user
from app.db.session import get_db
from app.models import User, UserRole
from app.schemas.torneio import (
    ClassificacaoPatch,
    DropRequest,
    ExternalTorneioCreate,
    JogadorCreate,
    MatchUpdate,
    TorneioCreateRequest,
    TorneioUpdate,
)
from app.services.torneio_service import TorneioError, TorneioService

router = APIRouter(prefix="/torneios", tags=["torneios"])


def get_torneio_service(db: Session = Depends(get_db)) -> TorneioService:
    return TorneioService(db)


def _player_payload(player) -> dict:
    return {
        "id": player.id,
        "name": player.name,
        "seed": player.seed,
        "registration_order": player.registration_order,
        "dropped_at": player.dropped_at.isoformat() if player.dropped_at else None,
        "decklist": player.decklist,
        "user_id": player.user_id,
        "attendance": getattr(player, "attendance", "checked_in"),
        "registration_source": getattr(player, "registration_source", "staff"),
    }


@router.post("")
def create_torneio(
    body: TorneioCreateRequest,
    user: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        event = svc.create_event(
            body.name,
            body.event_date,
            body.format,
            body.max_rounds,
            body.entry_fee,
            body.best_of,
            body.premiacao_preset_id,
            body.third_place_match,
            body.se_bo_config,
        )
        raw = svc._require_event(event.id)
        raw.created_by_user_id = user.id
        if body.registration_open:
            raw.registration_open = True
        svc._commit()
        return svc.get_event(event.id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/externos")
def create_external(
    body: ExternalTorneioCreate,
    user: RequireAdmin,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        event = svc.create_external_event(
            name=body.name,
            event_date=body.event_date,
            format=body.format,
            premiacao_preset_id=body.premiacao_preset_id,
            entry_fee=body.entry_fee,
            notes=body.notes,
            placements=[p.model_dump() for p in body.placements],
            created_by_user_id=user.id,
        )
        return svc.get_event(event.id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("")
def list_torneios(
    svc: TorneioService = Depends(get_torneio_service),
    _viewer: User | None = Depends(get_optional_user),
):
    return svc.list_events()


@router.get("/{event_id}")
def get_torneio(
    event_id: int,
    svc: TorneioService = Depends(get_torneio_service),
    _viewer: User | None = Depends(get_optional_user),
):
    try:
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{event_id}")
def update_torneio(
    event_id: int,
    body: TorneioUpdate,
    _: RequireStaff,
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
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        player = svc.add_player(
            event_id,
            body.name,
            body.seed,
            user_id=body.user_id,
            attendance=body.attendance,
            email=body.email,
            phone=body.phone,
            create_account=body.create_account,
        )
        return _player_payload(player)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/inscrever")
def self_inscribe(
    event_id: int,
    svc: TorneioService = Depends(get_torneio_service),
    user: User = Depends(get_current_user),
):
    if user.role not in {UserRole.player.value, UserRole.admin.value, UserRole.staff.value}:
        raise HTTPException(status_code=403, detail="Permissão insuficiente.")
    try:
        player = svc.self_register(event_id, user)
        return _player_payload(player)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/jogadores/{player_id}/check-in")
def check_in(
    event_id: int,
    player_id: int,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        return _player_payload(svc.check_in_player(event_id, player_id))
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{event_id}/jogadores/{player_id}", status_code=204)
def remove_jogador(
    event_id: int,
    player_id: int,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.remove_player(event_id, player_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/iniciar")
def iniciar(
    event_id: int,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.start_event(event_id)
        return svc.get_event(event_id)
    except (TorneioError, Exception) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{event_id}/rodadas")
def list_rodadas(
    event_id: int,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        return svc.get_rounds(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{event_id}/rodadas/{round_number}")
def get_rodada(
    event_id: int,
    round_number: int,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        return svc.get_round(event_id, round_number)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{event_id}/matches/{match_id}")
def update_partida(
    event_id: int,
    match_id: int,
    body: MatchUpdate,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.update_match(event_id, match_id, body.score_p1, body.score_p2)
        return {"ok": True}
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/avancar")
def avancar(
    event_id: int,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.complete_round(event_id)
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/iniciar-proxima-rodada")
def iniciar_proxima_rodada(
    event_id: int,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.start_next_round(event_id)
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/rodadas/reabrir")
def reabrir_rodada(
    event_id: int,
    _: RequireAdmin,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.reopen_round(event_id)
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/jogadores/{player_id}/drop", status_code=204)
def drop_jogador(
    event_id: int,
    player_id: int,
    body: DropRequest,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.drop_player(event_id, player_id, body.mid_round)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{event_id}/finalizar")
def finalizar(
    event_id: int,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.finalize(event_id)
        return svc.get_event(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{event_id}/classificacao")
def classificacao(
    event_id: int,
    svc: TorneioService = Depends(get_torneio_service),
    _viewer: User | None = Depends(get_optional_user),
):
    try:
        return svc.get_classificacao(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{event_id}/classificacao")
def patch_classificacao(
    event_id: int,
    body: ClassificacaoPatch,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.update_decklists(event_id, [u.model_dump() for u in body.updates])
        return svc.get_classificacao(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{event_id}/premiacao")
def premiacao_torneio(
    event_id: int,
    svc: TorneioService = Depends(get_torneio_service),
    _viewer: User | None = Depends(get_optional_user),
):
    try:
        return svc.get_premiacao(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{event_id}/export")
def export_log(
    event_id: int,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        data, filename = svc.export_log(event_id)
        return Response(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
