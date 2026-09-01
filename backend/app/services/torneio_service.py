"""Torneio business logic."""

from __future__ import annotations

import json
import random
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.premiacao.build_resultado import build_premiacao_resultado
from app.core.premiacao.presets import get_preset_config, load_presets
from app.core.premiacao.validation import ConfigError, validar_config
from app.core.torneios.models import BandMember
from app.core.torneios.se_phases import audit_se_bo_config, normalize_se_bo_config, resolve_best_of
from app.core.torneios.drops import (
    DropError,
    apply_mid_round_drop,
    validate_drop_between_rounds,
    validate_drop_mid_round,
)
from app.core.torneios.rounds import calcular_rodadas
from app.core.torneios.scores import ScoreError, match_is_decided, validate_score, wins_to_win
from app.core.torneios.standings import compute_se_standings, compute_standings
from app.core.torneios.state_machine import (
    StateMachineError,
    validate_complete_round,
    validate_finalize,
    validate_reopen_round,
    validate_start,
    validate_start_next_round,
)
from app.models import Event, Match, Player, Round
from app.models import PairingMode
from app.repositories.event_repository import EventRepository
from app.repositories.protocols import EventRepositoryProtocol


class TorneioError(ValueError):
    pass


class TorneioService:
    def __init__(self, db: Session, repo: EventRepositoryProtocol | None = None) -> None:
        self._db = db
        self._repo = repo or EventRepository(db)
        self._settings = get_settings()

    def _commit(self) -> None:
        try:
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise

    def _has_active_round(self, event: Event) -> bool:
        return any(r.status == "active" for r in event.rounds)

    def _get_active_round(self, event: Event) -> Round | None:
        return next((r for r in event.rounds if r.status == "active"), None)

    def _get_strategy(self, format: str):
        from app.core.torneios.pairing.pairing_se import SingleEliminationStrategy
        from app.core.torneios.pairing.pairing_swiss import SwissPairingStrategy

        if format == "single_elimination":
            return SingleEliminationStrategy()
        return SwissPairingStrategy()

    def _resolve_preset(self, preset_id: str) -> dict[str, Any]:
        store = load_presets(self._settings.resolved_presets_file)
        config = get_preset_config(store, preset_id)
        return {**store["presets"][preset_id]}

    def _normalize_name(self, name: str) -> str:
        return name.strip()

    def _pairing_mode(self, event: Event) -> str:
        return getattr(event, "pairing_mode", PairingMode.platform.value) or PairingMode.platform.value

    def _active_roster_players(self, event: Event) -> list[Player]:
        from app.models import Attendance

        return [
            p
            for p in event.players
            if getattr(p, "attendance", Attendance.checked_in.value) == Attendance.checked_in.value
            and not p.dropped_at
        ]

    def _pending_checkins(self, event: Event) -> int:
        from app.models import Attendance

        return sum(
            1
            for p in event.players
            if getattr(p, "attendance", Attendance.checked_in.value) == Attendance.pending.value
        )

    def _ensure_unique_event_name_date(
        self,
        name: str,
        event_date: date,
        exclude_id: int | None = None,
    ) -> None:
        normalized = self._normalize_name(name).casefold()
        for e in self._repo.list_all():
            if exclude_id and e.id == exclude_id:
                continue
            if self._normalize_name(e.name).casefold() == normalized and e.event_date == event_date:
                raise TorneioError(
                    f"Já existe um torneio '{name.strip()}' na data {event_date.isoformat()}."
                )

    def _ensure_unique_player_name(self, event: Event, name: str, exclude_id: int | None = None) -> None:
        normalized = self._normalize_name(name).casefold()
        for p in event.players:
            if exclude_id and p.id == exclude_id:
                continue
            if self._normalize_name(p.name).casefold() == normalized:
                raise TorneioError(f"Já existe um jogador '{name.strip()}' neste torneio.")

    def _ensure_unique_seed(self, event: Event, seed: int | None, exclude_id: int | None = None) -> None:
        if seed is None:
            return
        for p in event.players:
            if exclude_id and p.id == exclude_id:
                continue
            if p.seed == seed:
                raise TorneioError(f"Seed {seed} já está em uso neste torneio.")

    def _effective_best_of(self, match: Match, event: Event) -> int:
        return match.best_of or event.best_of

    def _match_has_result(self, match: Match, event: Event) -> bool:
        allow_draw = event.format == "swiss"
        best_of = self._effective_best_of(match, event)
        return match_is_decided(
            match.score_p1,
            match.score_p2,
            is_bye=match.is_bye,
            is_walkover=match.is_walkover,
            scores_submitted=match.scores_submitted,
            allow_draw=allow_draw,
            best_of=best_of,
        )

    def _validate_round_complete(self, event: Event, rnd: Round) -> None:
        for m in rnd.matches:
            if m.is_third_place and m.player2_id is None:
                continue
            if not self._match_has_result(m, event):
                raise TorneioError("Informe todos os resultados antes de concluir a rodada.")

    def _completed_rounds(self, event: Event) -> list[Round]:
        return sorted([r for r in event.rounds if r.status == "completed"], key=lambda r: r.number)

    def _swiss_rounds_done(self, event: Event) -> bool:
        return len(self._completed_rounds(event)) >= (event.max_rounds or 0)

    def _se_champion_count(self, event: Event) -> int:
        if not event.rounds:
            return 0
        last = max(event.rounds, key=lambda r: r.number)
        if last.status != "completed":
            return 999
        return sum(
            1
            for m in last.matches
            if not m.is_third_place and (m.is_bye or m.winner_id)
        )

    def _can_start_next_round(self, event: Event) -> bool:
        if event.status != "running" or self._has_active_round(event):
            return False
        if not self._completed_rounds(event):
            return False
        if event.format == "swiss":
            return not self._swiss_rounds_done(event)
        return self._se_champion_count(event) > 1

    def _can_reopen_round(self, event: Event) -> bool:
        if event.status != "running":
            return False
        active = self._get_active_round(event)
        if active and active.number > 1:
            return True
        return bool(self._completed_rounds(event))

    def _can_finalize(self, event: Event) -> bool:
        if event.status != "running" or self._has_active_round(event):
            return False
        if not event.rounds:
            return False
        for r in event.rounds:
            if r.status != "completed":
                return False
            for m in r.matches:
                if not self._match_has_result(m, event):
                    return False
        if event.format == "swiss":
            return self._swiss_rounds_done(event)
        return self._se_champion_count(event) <= 1

    def _event_phase(self, event: Event) -> dict[str, Any]:
        active = self._get_active_round(event)
        completed = self._completed_rounds(event)
        recommended = calcular_rodadas(
            len([p for p in event.players if not p.dropped_at]) or len(event.players)
        )
        return {
            "between_rounds": event.status == "running" and not active and bool(completed),
            "can_start_next_round": self._can_start_next_round(event),
            "can_finalize": self._can_finalize(event),
            "can_reopen_round": self._can_reopen_round(event),
            "recommended_rounds": recommended,
            "completed_rounds": len(completed),
        }

    def _is_legacy_finished(self, event: Event) -> bool:
        if event.status != "finished":
            return False
        pr = event.premiacao_resultado
        if not pr:
            return True
        return pr.get("schema_version", 1) < 2

    def create_event(
        self,
        name: str,
        event_date: date,
        format: str,
        max_rounds: int | None,
        entry_fee: float,
        best_of: int,
        premiacao_preset_id: str,
        third_place_match: bool = False,
        se_bo_config: dict[str, int] | None = None,
    ) -> Event:
        if format not in ("swiss", "single_elimination"):
            raise TorneioError("Formato inválido.")
        if best_of not in (1, 3, 5):
            raise TorneioError("Melhor de deve ser 1, 3 ou 5.")
        if format != "single_elimination":
            third_place_match = False
            se_bo_config = None
        clean_name = self._normalize_name(name)
        if not clean_name:
            raise TorneioError("Nome do torneio é obrigatório.")
        self._ensure_unique_event_name_date(clean_name, event_date)
        preset = self._resolve_preset(premiacao_preset_id)
        stored_bo = normalize_se_bo_config(se_bo_config) if se_bo_config else None
        if stored_bo:
            stored_bo = {str(k): v for k, v in stored_bo.items()}
        event = self._repo.create(
            name=clean_name,
            event_date=event_date,
            format=format,
            max_rounds=max_rounds,
            entry_fee=entry_fee,
            best_of=best_of,
            premiacao_preset=preset,
            shuffle_seed=random.randint(1, 2**31 - 1),
            third_place_match=third_place_match,
            se_bo_config=stored_bo,
        )
        self._commit()
        return event

    def list_events(self) -> list[dict[str, Any]]:
        return [self._event_summary(e) for e in self._repo.list_all()]

    def list_calendar_events(self, year: int, month: int) -> list[dict[str, Any]]:
        return [self._event_summary(e) for e in self._repo.list_by_month(year, month)]

    def get_event(self, event_id: int) -> dict[str, Any]:
        event = self._require_event(event_id)
        summary = self._event_summary(event)
        summary["players"] = [
            {
                "id": p.id,
                "name": p.name,
                "seed": p.seed,
                "dropped_at": p.dropped_at.isoformat() if p.dropped_at else None,
                "registration_order": p.registration_order,
                "decklist": p.decklist,
                "user_id": p.user_id,
                "attendance": getattr(p, "attendance", "checked_in"),
                "registration_source": getattr(p, "registration_source", "staff"),
            }
            for p in sorted(event.players, key=lambda x: x.registration_order)
        ]
        return summary

    def delete_event(self, event_id: int) -> None:
        event = self._require_event(event_id)
        self._repo.delete_event(event)
        self._commit()

    def update_event(self, event_id: int, data: dict[str, Any]) -> Event:
        event = self._require_event(event_id)
        if event.status != "draft":
            raise TorneioError("Só é possível editar torneios em rascunho.")
        new_name = event.name
        if "name" in data and data["name"] is not None:
            clean = self._normalize_name(data["name"])
            if not clean:
                raise TorneioError("Nome do torneio é obrigatório.")
            new_name = clean
        new_date = event.event_date
        if "event_date" in data and data["event_date"] is not None:
            new_date = data["event_date"]
        if new_name != event.name or new_date != event.event_date:
            self._ensure_unique_event_name_date(new_name, new_date, exclude_id=event.id)
        if "name" in data and data["name"] is not None:
            event.name = new_name
        for key in ("event_date", "entry_fee", "best_of"):
            if key in data and data[key] is not None:
                setattr(event, key, data[key])
        if "description" in data:
            raw = data["description"]
            event.description = (str(raw).strip() if raw is not None else "") or None
        if "start_time" in data:
            event.start_time = data["start_time"]
        if "tcg_game_id" in data:
            tcg_id = data["tcg_game_id"]
            if tcg_id is not None:
                from app.models import TcgGame

                game = self._db.query(TcgGame).filter(TcgGame.id == tcg_id).one_or_none()
                if game is None or not game.active:
                    raise TorneioError("TCG inválido.")
            event.tcg_game_id = tcg_id
        if "max_rounds" in data:
            event.max_rounds = data["max_rounds"]
        if event.format == "single_elimination":
            if "third_place_match" in data and data["third_place_match"] is not None:
                event.third_place_match = data["third_place_match"]
            if "se_bo_config" in data:
                raw = data["se_bo_config"]
                if raw is None:
                    event.se_bo_config = None
                else:
                    normalized = normalize_se_bo_config(raw)
                    event.se_bo_config = {str(k): v for k, v in normalized.items()} if normalized else None
        if "registration_open" in data and data["registration_open"] is not None:
            event.registration_open = bool(data["registration_open"])
        if "pairing_mode" in data and data["pairing_mode"] is not None:
            mode = data["pairing_mode"]
            if mode not in {PairingMode.platform.value, PairingMode.manual.value}:
                raise TorneioError("Modo de operação inválido.")
            event.pairing_mode = mode
        self._commit()
        return event

    def add_player(
        self,
        event_id: int,
        name: str,
        seed: int | None = None,
        *,
        user_id: int | None = None,
        attendance: str = "checked_in",
        registration_source: str = "staff",
        email: str | None = None,
        phone: str | None = None,
        create_account: bool = False,
    ) -> Player:
        from app.core.auth import AuthError, create_incomplete_user, get_user_by_email
        from app.core.auth.invite_delivery import provision_invite_and_email
        from app.models import Attendance, RegistrationSource, User

        event = self._require_event(event_id)
        if event.status != "draft":
            raise TorneioError("Só é possível adicionar jogadores em rascunho.")
        clean_name = self._normalize_name(name)
        if not clean_name:
            raise TorneioError("Nome do jogador é obrigatório.")
        if not create_account and user_id is None and not (email or "").strip():
            raise TorneioError(
                "Inscrição exige conta existente (user_id/e-mail) ou create_account com e-mail e celular."
            )
        self._ensure_unique_player_name(event, clean_name)
        self._ensure_unique_seed(event, seed)

        resolved_user_id = user_id
        if create_account:
            if not email or not phone:
                raise TorneioError("Cadastro rápido exige e-mail e celular.")
            try:
                user = create_incomplete_user(
                    self._db,
                    display_name=clean_name,
                    email=email,
                    phone=phone,
                )
                provision_invite_and_email(self._db, user)
            except AuthError as exc:
                raise TorneioError(str(exc)) from exc
            resolved_user_id = user.id
        elif user_id is not None:
            user = self._db.query(User).filter(User.id == user_id).one_or_none()
            if user is None:
                raise TorneioError("Conta de usuário não encontrada.")
            clean_name = user.display_name
            self._ensure_unique_player_name(event, clean_name)
        elif email:
            user = get_user_by_email(self._db, email)
            if not user:
                raise TorneioError("Conta não encontrada para este e-mail.")
            resolved_user_id = user.id
            clean_name = user.display_name
            self._ensure_unique_player_name(event, clean_name)

        if resolved_user_id is not None:
            dup = next((p for p in event.players if p.user_id == resolved_user_id), None)
            if dup:
                raise TorneioError("Este usuário já está inscrito neste torneio.")

        att = attendance if attendance in {Attendance.pending.value, Attendance.checked_in.value} else Attendance.checked_in.value
        src = (
            registration_source
            if registration_source in {RegistrationSource.staff.value, RegistrationSource.self.value}
            else RegistrationSource.staff.value
        )
        order = len(event.players) + 1
        player = self._repo.add_player(
            event_id,
            clean_name,
            seed,
            order,
            user_id=resolved_user_id,
            attendance=att,
            registration_source=src,
        )
        self._commit()
        return player

    def check_in_player(self, event_id: int, player_id: int) -> Player:
        from app.models import Attendance

        event = self._require_event(event_id)
        if event.status != "draft":
            raise TorneioError("Check-in só é permitido em rascunho.")
        player = next((p for p in event.players if p.id == player_id), None)
        if not player:
            raise TorneioError("Jogador não encontrado.")
        player.attendance = Attendance.checked_in.value
        self._commit()
        return player

    def self_register(self, event_id: int, user) -> Player:
        from app.models import Attendance, RegistrationSource

        event = self._require_event(event_id)
        if event.status != "draft":
            raise TorneioError("Inscrições só em rascunho.")
        if not event.registration_open:
            raise TorneioError("Inscrição pelo site indisponível para este torneio.")
        return self.add_player(
            event_id,
            user.display_name,
            user_id=user.id,
            attendance=Attendance.pending.value,
            registration_source=RegistrationSource.self.value,
        )

    def remove_player(self, event_id: int, player_id: int) -> None:
        event = self._require_event(event_id)
        if event.status != "draft":
            raise TorneioError("Só é possível remover jogadores em rascunho.")
        player = next((p for p in event.players if p.id == player_id), None)
        if not player:
            raise TorneioError("Jogador não encontrado.")
        self._repo.remove_player(player)
        self._commit()

    def start_event(self, event_id: int) -> Event:
        from app.models import Attendance

        event = self._require_event(event_id)
        if getattr(event, "source", "internal") == "external":
            raise TorneioError("Torneios externos não possuem rodadas internas.")
        if self._pairing_mode(event) == PairingMode.manual.value:
            raise TorneioError(
                "Este torneio opera sem rodadas na plataforma. Use registrar colocações."
            )
        pending = self._pending_checkins(event)
        state = self._repo.to_tournament_state(event)
        validate_start(state, pending_attendance=pending)

        try:
            checked = [
                p
                for p in event.players
                if getattr(p, "attendance", Attendance.checked_in.value) == Attendance.checked_in.value
                and not p.dropped_at
            ]
            active_count = len(checked)
            event.fp_n_at_start = active_count
            if event.max_rounds is None:
                event.max_rounds = calcular_rodadas(active_count)
            if event.format == "single_elimination" and event.se_bo_config:
                normalized = normalize_se_bo_config(event.se_bo_config)
                pruned, _warnings = audit_se_bo_config(normalized, event.max_rounds)
                event.se_bo_config = (
                    {str(k): v for k, v in pruned.items()} if pruned else None
                )
            event.registration_open = False
            event.status = "running"
            self._create_round(event, 1)
            self._commit()
        except Exception:
            self._repo.rollback()
            raise
        self._repo.refresh(event)
        return event

    def _create_round(self, event: Event, number: int) -> Round:
        state = self._repo.to_tournament_state(event)
        strategy = self._get_strategy(event.format)
        pairings = strategy.generate_pairings(state, number)

        rnd = Round(event_id=event.id, number=number, status="active")
        self._db.add(rnd)
        self._db.flush()

        max_rounds = event.max_rounds or number
        se_config = normalize_se_bo_config(event.se_bo_config)

        for pairing in pairings:
            match_bo = resolve_best_of(number, max_rounds, se_config, event.best_of)
            if pairing.is_third_place:
                match_bo = resolve_best_of(max_rounds, max_rounds, se_config, event.best_of)
            match = Match(
                round_id=rnd.id,
                player1_id=pairing.player1_id,
                player2_id=pairing.player2_id,
                is_bye=pairing.is_bye,
                had_rematch=pairing.had_rematch,
                is_third_place=pairing.is_third_place,
                best_of=match_bo,
                scores_submitted=pairing.is_bye,
            )
            if pairing.is_bye:
                w = wins_to_win(match_bo)
                match.score_p1 = w
                match.score_p2 = 0
                match.winner_id = pairing.player1_id
            self._db.add(match)

        return rnd

    def get_rounds(self, event_id: int) -> list[dict[str, Any]]:
        event = self._require_event(event_id)
        return [
            {"id": r.id, "number": r.number, "status": r.status}
            for r in sorted(event.rounds, key=lambda x: x.number)
        ]

    def get_round(self, event_id: int, number: int) -> dict[str, Any]:
        event = self._require_event(event_id)
        rnd = next((r for r in event.rounds if r.number == number), None)
        if not rnd:
            raise TorneioError("Rodada não encontrada.")
        state = self._repo.to_tournament_state(event)
        from app.core.torneios.standings import compute_match_records

        player_records = compute_match_records(state, before_round=number)
        players_map = {p.id: p.name for p in event.players}
        return {
            "id": rnd.id,
            "number": rnd.number,
            "status": rnd.status,
            "player_records": player_records,
            "matches": [
                {
                    "id": m.id,
                    "player1_id": m.player1_id,
                    "player1_name": players_map.get(m.player1_id, "?"),
                    "player2_id": m.player2_id,
                    "player2_name": players_map.get(m.player2_id) if m.player2_id else None,
                    "winner_id": m.winner_id,
                    "score_p1": m.score_p1,
                    "score_p2": m.score_p2,
                    "is_bye": m.is_bye,
                    "is_walkover": m.is_walkover,
                    "had_rematch": m.had_rematch,
                    "scores_submitted": m.scores_submitted,
                    "is_third_place": m.is_third_place,
                    "best_of": m.best_of or event.best_of,
                }
                for m in rnd.matches
            ],
        }

    def update_match(
        self,
        event_id: int,
        match_id: int,
        score_p1: int,
        score_p2: int,
    ) -> Match:
        event = self._require_event(event_id)
        match = self._find_match(event, match_id)
        if match.is_bye:
            raise TorneioError("Match de bye não aceita alteração.")
        if match.is_walkover:
            raise TorneioError("Resultado de WO não pode ser alterado.")
        rnd = next(r for r in event.rounds if r.id == match.round_id)
        if rnd.status != "active":
            raise TorneioError("Rodada não está ativa.")

        allow_draw = event.format == "swiss"
        best_of = self._effective_best_of(match, event)
        try:
            winner_side = validate_score(score_p1, score_p2, best_of, allow_draw=allow_draw)
        except ScoreError as exc:
            raise TorneioError(str(exc)) from exc

        match.score_p1 = score_p1
        match.score_p2 = score_p2
        match.scores_submitted = True
        if winner_side == 1:
            match.winner_id = match.player1_id
        elif winner_side == 2:
            match.winner_id = match.player2_id
        else:
            match.winner_id = None

        self._commit()
        return match

    def drop_player(self, event_id: int, player_id: int, mid_round: bool) -> None:
        event = self._require_event(event_id)
        player = next((p for p in event.players if p.id == player_id), None)
        if not player:
            raise TorneioError("Jogador não encontrado.")
        if player.dropped_at:
            raise TorneioError("Jogador já desistiu.")

        has_active = self._has_active_round(event)
        try:
            if mid_round:
                validate_drop_mid_round(event.status, has_active)
                active_round = next((r for r in event.rounds if r.status == "active"), None)
                assert active_round is not None
                in_bye = any(
                    m.is_bye and m.player1_id == player_id for m in active_round.matches
                )
                if not in_bye:
                    for m in active_round.matches:
                        if m.is_bye:
                            continue
                        if m.player1_id == player_id or m.player2_id == player_id:
                            dropped_is_p1 = m.player1_id == player_id
                            s1, s2 = apply_mid_round_drop(
                                m.score_p1, m.score_p2, dropped_is_p1, self._effective_best_of(m, event)
                            )
                            m.score_p1 = s1
                            m.score_p2 = s2
                            m.is_walkover = True
                            m.scores_submitted = True
                            m.winner_id = m.player2_id if dropped_is_p1 else m.player1_id
                            break
            else:
                validate_drop_between_rounds(event.status, has_active)

            player.dropped_at = datetime.utcnow()
            self._commit()
        except DropError as exc:
            self._repo.rollback()
            raise TorneioError(str(exc)) from exc
        except Exception:
            self._repo.rollback()
            raise

    def complete_round(self, event_id: int) -> Event:
        """Conclui rodada ativa; não inicia a próxima (janela para drop entre rodadas)."""
        event = self._require_event(event_id)
        state = self._repo.to_tournament_state(event)
        validate_complete_round(state)

        active = self._get_active_round(event)
        if not active:
            raise TorneioError("Nenhuma rodada ativa.")

        try:
            self._validate_round_complete(event, active)
            active.status = "completed"
            self._commit()
        except Exception:
            self._repo.rollback()
            raise
        self._repo.refresh(event)
        return event

    def start_next_round(self, event_id: int) -> Event:
        event = self._require_event(event_id)
        state = self._repo.to_tournament_state(event)
        validate_start_next_round(state)

        if not self._can_start_next_round(event):
            raise TorneioError("Não há próxima rodada a iniciar.")

        try:
            next_num = max(r.number for r in event.rounds) + 1
            self._create_round(event, next_num)
            self._commit()
        except Exception:
            self._repo.rollback()
            raise
        self._repo.refresh(event)
        return event

    def advance_round(self, event_id: int) -> Event:
        """Compat: conclui rodada ativa apenas."""
        return self.complete_round(event_id)

    def reopen_round(self, event_id: int, round_number: int | None = None) -> Event:
        """Reabre rodada concluída para correção de resultados.

        Se existir rodada posterior (ex.: R2 ativa após R1 concluída), remove-a
        antes de reativar a rodada alvo. Ao concluir e iniciar novamente, o pairing
        da rodada seguinte é recalculado.
        """
        event = self._require_event(event_id)
        state = self._repo.to_tournament_state(event)
        try:
            validate_reopen_round(state)
        except StateMachineError as exc:
            raise TorneioError(str(exc)) from exc

        active = self._get_active_round(event)
        completed = self._completed_rounds(event)

        if round_number is None:
            if active and active.number > 1:
                round_number = active.number - 1
            elif completed:
                round_number = completed[-1].number
            else:
                raise TorneioError("Nenhuma rodada para reabrir.")

        target = next((r for r in event.rounds if r.number == round_number), None)
        if not target:
            raise TorneioError("Rodada não encontrada.")
        if target.status != "completed":
            raise TorneioError("Só é possível reabrir rodadas concluídas.")

        try:
            for rnd in sorted(event.rounds, key=lambda r: r.number, reverse=True):
                if rnd.number <= round_number:
                    continue
                for match in list(rnd.matches):
                    self._db.delete(match)
                self._db.delete(rnd)
            self._db.flush()

            target.status = "active"
            self._commit()
        except Exception:
            self._repo.rollback()
            raise
        self._repo.refresh(event)
        return event

    def finalize(self, event_id: int) -> Event:
        event = self._require_event(event_id)
        state = self._repo.to_tournament_state(event)
        validate_finalize(state)

        if not self._can_finalize(event):
            raise TorneioError(
                "Só é possível finalizar quando todas as rodadas e partidas estiverem concluídas."
            )

        n = len(event.players)
        config = {k: v for k, v in event.premiacao_preset.items() if k != "label"}
        try:
            validar_config({**config, "label": "x"})
        except ConfigError as exc:
            raise TorneioError(f"Preset de premiação inválido no evento: {exc}") from exc

        decklists = {p.id: p.decklist for p in event.players}
        state = self._repo.to_tournament_state(event)
        if event.format == "single_elimination":
            standings = compute_se_standings(state, decklists)
        else:
            standings = compute_standings(state, decklists)

        members = [
            BandMember(
                player_id=s.player_id,
                band_label=s.rank_label or f"{s.rank}º",
                is_drop=s.is_drop,
                name=s.name,
            )
            for s in standings
            if not s.is_drop
        ]
        snapshot = [
            {
                "rank": s.rank,
                "player_id": s.player_id,
                "name": s.name,
                "points": s.points,
                "omw": s.omw,
                "gw": s.gw,
                "ogw": s.ogw,
                "decklist": s.decklist,
                "is_drop": s.is_drop,
                "rank_label": s.rank_label,
            }
            for s in standings
        ]

        event.premiacao_resultado = build_premiacao_resultado(
            format=event.format,
            n=n,
            config=config,
            third_place_match=event.third_place_match,
            members=members,
            standings_snapshot=snapshot,
            entry_fee=event.entry_fee,
        )
        event.status = "finished"
        self._commit()
        self._award_fourse_points(event, standings)
        return event

    def finalize_manual_placements(
        self,
        event_id: int,
        placements: list[dict[str, Any]],
    ) -> Event:
        from app.core.auth.fourse_points import compute_fp_awards, replace_event_fp_ledger

        event = self._require_event(event_id)
        if event.status != "draft":
            raise TorneioError("Só é possível registrar colocações em torneios em rascunho.")
        if self._pairing_mode(event) != PairingMode.manual.value:
            raise TorneioError("Este torneio não está em modo sem rodadas.")
        pending = self._pending_checkins(event)
        if pending > 0:
            raise TorneioError(
                f"Há {pending} inscrição(ões) pendente(s) de check-in. "
                "Confirme a presença ou remova os ausentes antes de finalizar."
            )
        if not placements:
            raise TorneioError("Informe ao menos uma colocação.")

        players_by_id = {p.id: p for p in event.players}
        active_ids = {p.id for p in self._active_roster_players(event)}
        if not active_ids:
            raise TorneioError("Informe ao menos um jogador com check-in.")

        rows_by_player: dict[int, dict[str, Any]] = {}
        for row in placements:
            pid = int(row["player_id"])
            if pid not in players_by_id:
                raise TorneioError(f"Jogador {pid} não encontrado neste torneio.")
            if pid in rows_by_player:
                raise TorneioError(f"Colocação duplicada para o jogador {pid}.")
            rows_by_player[pid] = row

        if set(rows_by_player.keys()) != active_ids:
            missing = active_ids - set(rows_by_player.keys())
            extra = set(rows_by_player.keys()) - active_ids
            if missing:
                names = ", ".join(players_by_id[i].name for i in sorted(missing))
                raise TorneioError(f"Faltando colocação para: {names}.")
            if extra:
                raise TorneioError("Há colocações para jogadores sem check-in ou removidos.")

        non_drop_placements: list[int] = []
        for row in rows_by_player.values():
            if row.get("is_drop"):
                continue
            placement = int(row["placement"])
            non_drop_placements.append(placement)

        if not non_drop_placements:
            raise TorneioError("Informe ao menos uma colocação válida (não-drop).")
        if len(set(non_drop_placements)) != len(non_drop_placements):
            raise TorneioError("Colocações duplicadas entre jogadores não-drop.")
        if min(non_drop_placements) < 1:
            raise TorneioError("Colocações devem ser maiores que zero.")

        preset = event.premiacao_preset or {}
        config = {k: v for k, v in preset.items() if k != "label"}
        try:
            validar_config({**config, "label": "x"})
        except ConfigError as exc:
            raise TorneioError(f"Preset de premiação inválido no evento: {exc}") from exc

        standings_snapshot: list[dict[str, Any]] = []
        members: list[BandMember] = []
        fp_placements: list[dict[str, Any]] = []

        sorted_rows = sorted(
            rows_by_player.values(),
            key=lambda r: (bool(r.get("is_drop")), int(r["placement"])),
        )
        for row in sorted_rows:
            player = players_by_id[int(row["player_id"])]
            is_drop = bool(row.get("is_drop"))
            if "decklist" in row:
                raw_deck = row.get("decklist")
                player.decklist = (str(raw_deck).strip() if raw_deck is not None else "") or None
            placement = int(row["placement"])
            standings_snapshot.append(
                {
                    "rank": None if is_drop else placement,
                    "player_id": player.id,
                    "name": player.name,
                    "points": 0,
                    "omw": 0,
                    "gw": 0,
                    "ogw": 0,
                    "decklist": player.decklist,
                    "is_drop": is_drop,
                    "rank_label": "DROP" if is_drop else f"{placement}º",
                }
            )
            if not is_drop:
                members.append(
                    BandMember(
                        player_id=player.id,
                        band_label=f"{placement}º",
                        is_drop=False,
                        name=player.name,
                    )
                )
            if player.user_id:
                fp_placements.append(
                    {
                        "user_id": player.user_id,
                        "placement": None if is_drop else placement,
                        "is_drop": is_drop,
                    }
                )

        n = len(non_drop_placements)
        event.fp_n_at_start = n
        event.registration_open = False
        event.premiacao_resultado = build_premiacao_resultado(
            format=event.format,
            n=n,
            config=config,
            third_place_match=event.third_place_match,
            members=members,
            standings_snapshot=standings_snapshot,
            entry_fee=event.entry_fee,
        )
        event.status = "finished"
        self._commit()
        awards = compute_fp_awards(n=n, config=preset, placements=fp_placements)
        replace_event_fp_ledger(self._db, event.id, awards)
        return event

    def _award_fourse_points(self, event: Event, standings) -> None:
        from app.core.auth.fourse_points import compute_fp_awards, replace_event_fp_ledger

        n = event.fp_n_at_start or len(
            [p for p in event.players if getattr(p, "attendance", "checked_in") == "checked_in"]
        )
        players_by_id = {p.id: p for p in event.players}
        # Paid placement index among non-drops only
        non_drop_rank = 0
        placements: list[dict] = []
        for s in standings:
            player = players_by_id.get(s.player_id)
            if not player or not player.user_id:
                continue
            if s.is_drop:
                placements.append(
                    {"user_id": player.user_id, "placement": None, "is_drop": True}
                )
                continue
            non_drop_rank += 1
            placements.append(
                {"user_id": player.user_id, "placement": non_drop_rank, "is_drop": False}
            )
        awards = compute_fp_awards(n=n, config=event.premiacao_preset or {}, placements=placements)
        replace_event_fp_ledger(self._db, event.id, awards)

    def get_classificacao(self, event_id: int) -> list[dict[str, Any]]:
        event = self._require_event(event_id)
        if (
            event.status == "finished"
            and event.premiacao_resultado
            and event.premiacao_resultado.get("schema_version", 1) >= 2
            and "standings_snapshot" in event.premiacao_resultado
        ):
            return event.premiacao_resultado["standings_snapshot"]

        state = self._repo.to_tournament_state(event)
        decklists = {p.id: p.decklist for p in event.players}
        if event.format == "single_elimination" and not self._is_legacy_finished(event):
            standings = compute_se_standings(state, decklists)
        else:
            standings = compute_standings(state, decklists)
        return [
            {
                "rank": s.rank,
                "player_id": s.player_id,
                "name": s.name,
                "points": s.points,
                "omw": s.omw,
                "gw": s.gw,
                "ogw": s.ogw,
                "decklist": s.decklist,
                "is_drop": s.is_drop,
                "rank_label": s.rank_label,
            }
            for s in standings
        ]

    def update_decklists(self, event_id: int, updates: list[dict[str, Any]]) -> None:
        event = self._require_event(event_id)
        if event.status != "finished":
            raise TorneioError("Decklists só após finalizar.")
        for u in updates:
            player = next((p for p in event.players if p.id == u["player_id"]), None)
            if player:
                player.decklist = u.get("decklist")
        self._commit()

    def get_premiacao(self, event_id: int) -> dict[str, Any]:
        event = self._require_event(event_id)
        if not event.premiacao_resultado:
            raise TorneioError("Premiação não calculada.")
        return event.premiacao_resultado

    def export_log(self, event_id: int) -> tuple[bytes, str]:
        event = self._require_event(event_id)
        if event.status != "finished":
            raise TorneioError("Export disponível apenas após finalizar o torneio.")
        if not event.premiacao_resultado:
            raise TorneioError("Premiação não calculada.")

        standings = self.get_classificacao(event_id)
        players_map = {p.id: p for p in event.players}
        now = datetime.utcnow()

        log = {
            "version": 2,
            "exported_at": now.isoformat() + "Z",
            "premiacao_schema_version": event.premiacao_resultado.get("schema_version", 1),
            "event": {
                "id": event.id,
                "name": event.name,
                "event_date": event.event_date.isoformat(),
                "format": event.format,
                "max_rounds": event.max_rounds,
                "entry_fee": event.entry_fee,
                "best_of": event.best_of,
                "third_place_match": event.third_place_match,
                "se_bo_config": event.se_bo_config,
                "status": event.status,
                "premiacao_preset": event.premiacao_preset,
            },
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "seed": p.seed,
                    "decklist": p.decklist,
                    "dropped_at": p.dropped_at.isoformat() if p.dropped_at else None,
                }
                for p in event.players
            ],
            "rounds": [
                {
                    "number": r.number,
                    "status": r.status,
                    "matches": [
                        {
                            "player1_id": m.player1_id,
                            "player2_id": m.player2_id,
                            "player1": players_map[m.player1_id].name,
                            "player2": players_map[m.player2_id].name if m.player2_id else None,
                            "winner_id": m.winner_id,
                            "score": f"{m.score_p1}-{m.score_p2}",
                            "bye": m.is_bye,
                            "walkover": m.is_walkover,
                            "had_rematch": m.had_rematch,
                            "is_third_place": m.is_third_place,
                            "best_of": m.best_of or event.best_of,
                        }
                        for m in r.matches
                    ],
                }
                for r in sorted(event.rounds, key=lambda x: x.number)
            ],
            "standings": standings,
            "premiacao": event.premiacao_resultado,
        }

        content = json.dumps(log, indent=2, ensure_ascii=False).encode("utf-8")
        ts = now.strftime("%Y_%m_%d_%H_%M")
        filename = f"torneio_{event.id}_{event.event_date.isoformat()}_{ts}.json"
        logs_dir = self._settings.resolved_logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / filename).write_bytes(content)
        return content, filename

    def _require_event(self, event_id: int) -> Event:
        event = self._repo.get(event_id)
        if not event:
            raise TorneioError("Torneio não encontrado.")
        return event

    def _find_match(self, event: Event, match_id: int) -> Match:
        for r in event.rounds:
            for m in r.matches:
                if m.id == match_id:
                    return m
        raise TorneioError("Match não encontrado.")

    def _event_summary(self, event: Event) -> dict[str, Any]:
        current = 0
        for r in event.rounds:
            if r.status == "active":
                current = r.number
        if not current:
            completed = [r.number for r in event.rounds if r.status == "completed"]
            current = max(completed, default=0)

        phase = self._event_phase(event)
        summary = {
            "id": event.id,
            "name": event.name,
            "event_date": event.event_date.isoformat(),
            "format": event.format,
            "max_rounds": event.max_rounds,
            "entry_fee": event.entry_fee,
            "best_of": event.best_of,
            "third_place_match": event.third_place_match,
            "se_bo_config": event.se_bo_config,
            "status": event.status,
            "source": getattr(event, "source", "internal"),
            "pairing_mode": self._pairing_mode(event),
            "registration_open": bool(getattr(event, "registration_open", False)),
            "fp_n_at_start": getattr(event, "fp_n_at_start", None),
            "description": getattr(event, "description", None),
            "start_time": getattr(event, "start_time", None),
            "tcg_game_id": getattr(event, "tcg_game_id", None),
            "tcg_game": None,
            "player_count": len(event.players),
            "participant_user_ids": [
                p.user_id for p in event.players if getattr(p, "user_id", None) is not None
            ],
            "pending_checkins": sum(
                1 for p in event.players if getattr(p, "attendance", "checked_in") == "pending"
            ),
            "current_round": current,
            **phase,
        }
        tcg = getattr(event, "tcg_game", None)
        if tcg is not None:
            summary["tcg_game"] = {
                "id": tcg.id,
                "name": tcg.name,
                "slug": tcg.slug,
                "color_hex": tcg.color_hex,
            }
        if event.status == "draft" and event.format == "single_elimination":
            max_r = event.max_rounds or calcular_rodadas(
                len([p for p in event.players if not p.dropped_at]) or len(event.players) or 4
            )
            _, warnings = audit_se_bo_config(
                normalize_se_bo_config(event.se_bo_config), max_r
            )
            if warnings:
                summary["config_warnings"] = warnings
        return summary

    def create_external_event(
        self,
        *,
        name: str,
        event_date: date,
        format: str,
        premiacao_preset_id: str,
        entry_fee: float,
        notes: str | None,
        placements: list[dict[str, Any]],
        created_by_user_id: int | None = None,
        tcg_game_id: int | None = None,
    ) -> Event:
        """Admin import of an external tournament for FP + public history."""
        from app.core.auth import AuthError, create_incomplete_user
        from app.core.auth.invite_delivery import provision_invite_and_email
        from app.core.auth.fourse_points import compute_fp_awards, replace_event_fp_ledger
        from app.models import Attendance, EventSource, RegistrationSource, User

        if format not in ("swiss", "single_elimination"):
            raise TorneioError("Formato inválido.")
        if len(placements) < 1:
            raise TorneioError("Informe ao menos uma colocação.")
        clean_name = self._normalize_name(name)
        if not clean_name:
            raise TorneioError("Nome do torneio é obrigatório.")
        self._ensure_unique_event_name_date(clean_name, event_date)
        preset = self._resolve_preset(premiacao_preset_id)
        event = self._repo.create(
            name=clean_name,
            event_date=event_date,
            format=format,
            max_rounds=None,
            entry_fee=entry_fee,
            best_of=3,
            premiacao_preset=preset,
            shuffle_seed=1,
            third_place_match=False,
            se_bo_config=None,
        )
        event.source = EventSource.external.value
        event.external_notes = notes
        event.created_by_user_id = created_by_user_id
        if tcg_game_id is not None:
            event.tcg_game_id = tcg_game_id
        event.registration_open = False
        self._db.flush()

        standings_snapshot: list[dict[str, Any]] = []
        members: list[BandMember] = []
        fp_placements: list[dict[str, Any]] = []
        order = 0
        for row in sorted(placements, key=lambda r: (bool(r.get("is_drop")), int(r["placement"]))):
            order += 1
            display = self._normalize_name(row["display_name"])
            user_id = row.get("user_id")
            if row.get("create_account"):
                try:
                    user = create_incomplete_user(
                        self._db,
                        display_name=display,
                        email=row["email"],
                        phone=row["phone"],
                    )
                    provision_invite_and_email(self._db, user)
                except AuthError as exc:
                    raise TorneioError(str(exc)) from exc
                user_id = user.id
            elif user_id:
                user = self._db.query(User).filter(User.id == user_id).one_or_none()
                if not user:
                    raise TorneioError(f"Usuário {user_id} não encontrado.")
                display = user.display_name
            player = self._repo.add_player(
                event.id,
                display,
                None,
                order,
                user_id=user_id,
                attendance=Attendance.checked_in.value,
                registration_source=RegistrationSource.staff.value,
            )
            player.decklist = row.get("decklist")
            is_drop = bool(row.get("is_drop"))
            standings_snapshot.append(
                {
                    "rank": None if is_drop else row["placement"],
                    "player_id": player.id,
                    "name": display,
                    "points": 0,
                    "omw": 0,
                    "gw": 0,
                    "ogw": 0,
                    "decklist": player.decklist,
                    "is_drop": is_drop,
                    "rank_label": "DROP" if is_drop else f"{row['placement']}º",
                }
            )
            if not is_drop:
                members.append(
                    BandMember(
                        player_id=player.id,
                        band_label=f"{row['placement']}º",
                        is_drop=False,
                        name=display,
                    )
                )
            if user_id:
                fp_placements.append(
                    {
                        "user_id": user_id,
                        "placement": None if is_drop else row["placement"],
                        "is_drop": is_drop,
                    }
                )

        n = sum(1 for r in placements if not r.get("is_drop"))
        event.fp_n_at_start = n
        config = {k: v for k, v in preset.items() if k != "label"}
        event.premiacao_resultado = build_premiacao_resultado(
            format=format,
            n=n,
            config=config,
            third_place_match=False,
            members=members,
            standings_snapshot=standings_snapshot,
            entry_fee=entry_fee,
        )
        event.status = "finished"
        self._commit()
        awards = compute_fp_awards(n=n, config=preset, placements=fp_placements)
        replace_event_fp_ledger(self._db, event.id, awards)
        return event
