"""Torneio business logic."""

from __future__ import annotations

import json
import random
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.premiacao.calculator import calcular
from app.core.premiacao.presets import get_preset_config, load_presets
from app.core.premiacao.validation import ConfigError, validar_config
from app.core.torneios.drops import (
    DropError,
    apply_mid_round_drop,
    validate_drop_between_rounds,
    validate_drop_mid_round,
)
from app.core.torneios.rounds import calcular_rodadas
from app.core.torneios.scores import ScoreError, match_is_decided, validate_score, wins_to_win
from app.core.torneios.standings import compute_standings
from app.core.torneios.state_machine import (
    StateMachineError,
    validate_complete_round,
    validate_finalize,
    validate_reopen_round,
    validate_start,
    validate_start_next_round,
)
from app.models import Event, Match, Player, Round
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

    def _ensure_unique_event_name(self, name: str, exclude_id: int | None = None) -> None:
        normalized = self._normalize_name(name).casefold()
        for e in self._repo.list_all():
            if exclude_id and e.id == exclude_id:
                continue
            if self._normalize_name(e.name).casefold() == normalized:
                raise TorneioError(f"Já existe um torneio com o nome '{name.strip()}'.")

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

    def _match_has_result(self, match: Match, event: Event) -> bool:
        allow_draw = event.format == "swiss"
        return match_is_decided(
            match.score_p1,
            match.score_p2,
            is_bye=match.is_bye,
            is_walkover=match.is_walkover,
            scores_submitted=match.scores_submitted,
            allow_draw=allow_draw,
            best_of=event.best_of,
        )

    def _validate_round_complete(self, event: Event, rnd: Round) -> None:
        for m in rnd.matches:
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
        return sum(1 for m in last.matches if m.is_bye or m.winner_id)

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

    def create_event(
        self,
        name: str,
        event_date: date,
        format: str,
        max_rounds: int | None,
        entry_fee: float,
        best_of: int,
        premiacao_preset_id: str,
    ) -> Event:
        if format not in ("swiss", "single_elimination"):
            raise TorneioError("Formato inválido.")
        if best_of not in (1, 3, 5):
            raise TorneioError("Melhor de deve ser 1, 3 ou 5.")
        clean_name = self._normalize_name(name)
        if not clean_name:
            raise TorneioError("Nome do torneio é obrigatório.")
        self._ensure_unique_event_name(clean_name)
        preset = self._resolve_preset(premiacao_preset_id)
        event = self._repo.create(
            name=clean_name,
            event_date=event_date,
            format=format,
            max_rounds=max_rounds,
            entry_fee=entry_fee,
            best_of=best_of,
            premiacao_preset=preset,
            shuffle_seed=random.randint(1, 2**31 - 1),
        )
        self._commit()
        return event

    def list_events(self) -> list[dict[str, Any]]:
        return [self._event_summary(e) for e in self._repo.list_all()]

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
            }
            for p in sorted(event.players, key=lambda x: x.registration_order)
        ]
        return summary

    def update_event(self, event_id: int, data: dict[str, Any]) -> Event:
        event = self._require_event(event_id)
        if event.status != "draft":
            raise TorneioError("Só é possível editar torneios em rascunho.")
        if "name" in data and data["name"] is not None:
            clean = self._normalize_name(data["name"])
            if not clean:
                raise TorneioError("Nome do torneio é obrigatório.")
            self._ensure_unique_event_name(clean, exclude_id=event.id)
            event.name = clean
        for key in ("event_date", "entry_fee", "best_of"):
            if key in data and data[key] is not None:
                setattr(event, key, data[key])
        if "max_rounds" in data and data["max_rounds"] is not None:
            event.max_rounds = data["max_rounds"]
        self._commit()
        return event

    def add_player(self, event_id: int, name: str, seed: int | None = None) -> Player:
        event = self._require_event(event_id)
        if event.status != "draft":
            raise TorneioError("Só é possível adicionar jogadores em rascunho.")
        clean_name = self._normalize_name(name)
        if not clean_name:
            raise TorneioError("Nome do jogador é obrigatório.")
        self._ensure_unique_player_name(event, clean_name)
        self._ensure_unique_seed(event, seed)
        order = len(event.players) + 1
        player = self._repo.add_player(event_id, clean_name, seed, order)
        self._commit()
        return player

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
        event = self._require_event(event_id)
        state = self._repo.to_tournament_state(event)
        validate_start(state)

        try:
            active_count = len([p for p in event.players if not p.dropped_at])
            if event.max_rounds is None:
                event.max_rounds = calcular_rodadas(active_count)
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

        for pairing in pairings:
            match = Match(
                round_id=rnd.id,
                player1_id=pairing.player1_id,
                player2_id=pairing.player2_id,
                is_bye=pairing.is_bye,
                had_rematch=pairing.had_rematch,
                scores_submitted=pairing.is_bye,
            )
            if pairing.is_bye:
                w = wins_to_win(event.best_of)
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
        try:
            winner_side = validate_score(score_p1, score_p2, event.best_of, allow_draw=allow_draw)
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
                                m.score_p1, m.score_p2, dropped_is_p1, event.best_of
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

        resultado = calcular(n, config)
        creditos: list[float] = []
        if event.entry_fee > 0:
            creditos = [
                round(p * event.entry_fee, config["casas_decimais"]) for p in resultado["premios"]
            ]

        event.premiacao_resultado = {
            **resultado,
            "entry_fee": event.entry_fee,
            "creditos": creditos if creditos else None,
        }
        event.status = "finished"
        self._commit()
        return event

    def get_classificacao(self, event_id: int) -> list[dict[str, Any]]:
        event = self._require_event(event_id)
        state = self._repo.to_tournament_state(event)
        decklists = {p.id: p.decklist for p in event.players}
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
            "version": 1,
            "exported_at": now.isoformat() + "Z",
            "event": {
                "id": event.id,
                "name": event.name,
                "event_date": event.event_date.isoformat(),
                "format": event.format,
                "max_rounds": event.max_rounds,
                "entry_fee": event.entry_fee,
                "best_of": event.best_of,
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
                            "player1": players_map[m.player1_id].name,
                            "player2": players_map[m.player2_id].name if m.player2_id else None,
                            "score": f"{m.score_p1}-{m.score_p2}",
                            "bye": m.is_bye,
                            "walkover": m.is_walkover,
                            "had_rematch": m.had_rematch,
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
        return {
            "id": event.id,
            "name": event.name,
            "event_date": event.event_date.isoformat(),
            "format": event.format,
            "max_rounds": event.max_rounds,
            "entry_fee": event.entry_fee,
            "best_of": event.best_of,
            "status": event.status,
            "player_count": len(event.players),
            "current_round": current,
            **phase,
        }
