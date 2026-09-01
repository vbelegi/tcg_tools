"""Torneios API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireStaff, get_current_user, get_optional_user
from app.api.v1.event_visibility import filter_calendar_tournaments
from app.db.session import get_db
from app.models import Player, User, UserRole
from app.schemas.torneio import (
    ClassificacaoPatch,
    DropRequest,
    ExternalTorneioCreate,
    JogadorCreate,
    ManualFinalizeRequest,
    MatchUpdate,
    TorneioCreateRequest,
    TorneioUpdate,
)
from app.core.torneios.state_machine import StateMachineError
from app.services.torneio_service import TorneioError, TorneioService

router = APIRouter(prefix="/torneios", tags=["torneios"])


def get_torneio_service(db: Session = Depends(get_db)) -> TorneioService:
    return TorneioService(db)


def _role_value(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _is_staff_user(user: User) -> bool:
    return _role_value(user) in {UserRole.admin.value, UserRole.staff.value}


def _registered_event_ids(db: Session, user_id: int) -> set[int]:
    rows = db.query(Player.event_id).filter(Player.user_id == user_id).all()
    return {int(r[0]) for r in rows}


def _can_view_event(
    viewer: User | None,
    *,
    event_id: int,
    status: str,
    registration_open: bool = False,
    registered_ids: set[int] | None = None,
    db: Session | None = None,
) -> bool:
    open_draft = status == "draft" and registration_open
    if viewer is None:
        return status == "finished" or open_draft
    if _is_staff_user(viewer):
        return True
    if status == "finished" or open_draft:
        return True
    if registered_ids is not None:
        return event_id in registered_ids
    if db is None:
        return False
    return (
        db.query(Player.id)
        .filter(Player.event_id == event_id, Player.user_id == viewer.id)
        .first()
        is not None
    )


def _ensure_can_view_event(
    viewer: User | None,
    *,
    event_id: int,
    status: str,
    db: Session,
    registration_open: bool = False,
) -> None:
    if not _can_view_event(
        viewer,
        event_id=event_id,
        status=status,
        registration_open=registration_open,
        db=db,
    ):
        raise HTTPException(status_code=404, detail="Torneio não encontrado.")


def _is_public_list_event(event: dict) -> bool:
    status = event.get("status")
    if status == "finished":
        return True
    return status == "draft" and bool(event.get("registration_open"))


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
        from app.models import TcgGame

        game = svc._db.query(TcgGame).filter(TcgGame.id == body.tcg_game_id).one_or_none()
        if game is None or not game.active:
            raise HTTPException(status_code=422, detail="TCG inválido.")
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
        raw.registration_open = bool(body.registration_open)
        raw.description = (body.description or "").strip() or None
        raw.start_time = body.start_time
        raw.tcg_game_id = body.tcg_game_id
        raw.pairing_mode = body.pairing_mode
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
        from app.models import TcgGame

        game = svc._db.query(TcgGame).filter(TcgGame.id == body.tcg_game_id).one_or_none()
        if game is None or not game.active:
            raise HTTPException(status_code=422, detail="TCG inválido.")
        event = svc.create_external_event(
            name=body.name,
            event_date=body.event_date,
            format=body.format,
            premiacao_preset_id=body.premiacao_preset_id,
            entry_fee=body.entry_fee,
            notes=body.notes,
            placements=[p.model_dump() for p in body.placements],
            created_by_user_id=user.id,
            tcg_game_id=body.tcg_game_id,
        )
        return svc.get_event(event.id)
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("")
def list_torneios(
    svc: TorneioService = Depends(get_torneio_service),
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    events = svc.list_events()
    if viewer is None:
        return [e for e in events if _is_public_list_event(e)]
    if _is_staff_user(viewer):
        return events
    registered = _registered_event_ids(db, viewer.id)
    return [
        e
        for e in events
        if _is_public_list_event(e) or int(e["id"]) in registered
    ]


@router.get("/calendar")
def calendar_torneios(
    year: int,
    month: int,
    svc: TorneioService = Depends(get_torneio_service),
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=422, detail="Mês inválido.")
    if year < 2000 or year > 2100:
        raise HTTPException(status_code=422, detail="Ano inválido.")
    events = svc.list_calendar_events(year, month)
    return filter_calendar_tournaments(events, viewer, db)


@router.get("/{event_id}")
def get_torneio(
    event_id: int,
    svc: TorneioService = Depends(get_torneio_service),
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    try:
        data = svc.get_event(event_id)
        _ensure_can_view_event(
            viewer,
            event_id=event_id,
            status=data.get("status", ""),
            registration_open=bool(data.get("registration_open")),
            db=db,
        )
        return data
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{event_id}", status_code=204)
def delete_torneio(
    event_id: int,
    _: RequireAdmin,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.delete_event(event_id)
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
    except (TorneioError, StateMachineError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Não foi possível iniciar o torneio.") from exc


@router.get("/{event_id}/rodadas")
def list_rodadas(
    event_id: int,
    svc: TorneioService = Depends(get_torneio_service),
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    try:
        event = svc.get_event(event_id)
        _ensure_can_view_event(
            viewer,
            event_id=event_id,
            status=event.get("status", ""),
            registration_open=bool(event.get("registration_open")),
            db=db,
        )
        return svc.get_rounds(event_id)
    except TorneioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{event_id}/rodadas/{round_number}")
def get_rodada(
    event_id: int,
    round_number: int,
    svc: TorneioService = Depends(get_torneio_service),
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    try:
        event = svc.get_event(event_id)
        _ensure_can_view_event(
            viewer,
            event_id=event_id,
            status=event.get("status", ""),
            registration_open=bool(event.get("registration_open")),
            db=db,
        )
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


@router.post("/{event_id}/finalizar-colocacoes")
def finalizar_colocacoes(
    event_id: int,
    body: ManualFinalizeRequest,
    _: RequireStaff,
    svc: TorneioService = Depends(get_torneio_service),
):
    try:
        svc.finalize_manual_placements(
            event_id,
            [p.model_dump() for p in body.placements],
        )
        return svc.get_event(event_id)
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
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    try:
        event = svc.get_event(event_id)
        _ensure_can_view_event(
            viewer,
            event_id=event_id,
            status=event.get("status", ""),
            registration_open=bool(event.get("registration_open")),
            db=db,
        )
        return {"standings": svc.get_classificacao(event_id)}
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
        return {"standings": svc.get_classificacao(event_id)}
    except TorneioError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{event_id}/premiacao")
def premiacao_torneio(
    event_id: int,
    svc: TorneioService = Depends(get_torneio_service),
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    try:
        event = svc.get_event(event_id)
        _ensure_can_view_event(
            viewer,
            event_id=event_id,
            status=event.get("status", ""),
            registration_open=bool(event.get("registration_open")),
            db=db,
        )
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
