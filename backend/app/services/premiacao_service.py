"""Premiação business logic."""

from __future__ import annotations

import csv
import io
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from app import paths
from app.config import Settings, get_settings
from app.core.premiacao.calculator import calcular
from app.core.premiacao.presets import (
    get_preset_config,
    load_presets,
    save_presets,
)
from app.core.premiacao.validation import (
    ConfigError,
    InputError,
    validar_jogadores,
    validar_limite_tabela,
    validar_valor_inscricao,
)


class PremiacaoService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._legacy_path = paths.legacy_settings_file()

    @property
    def presets_path(self) -> Path:
        return self._settings.resolved_presets_file

    def _load(self) -> dict[str, Any]:
        return load_presets(self.presets_path, self._legacy_path)

    def list_presets(self) -> dict[str, Any]:
        return self._load()

    def get_preset(self, preset_id: str) -> dict[str, Any]:
        store = self._load()
        if preset_id not in store["presets"]:
            raise ConfigError(f"Preset '{preset_id}' não encontrado.")
        return deepcopy(store["presets"][preset_id])

    def presets_mtime(self) -> float | None:
        if not self.presets_path.exists():
            return None
        return self.presets_path.stat().st_mtime

    def update_preset(
        self, preset_id: str, data: dict[str, Any], expected_mtime: float | None = None
    ) -> dict[str, Any]:
        if expected_mtime is not None:
            current = self.presets_mtime()
            if current is not None and abs(current - expected_mtime) > 0.001:
                raise ConfigError(
                    "Presets foram alterados em outra aba. Recarregue antes de salvar."
                )
        store = self._load()
        if preset_id not in store["presets"]:
            raise ConfigError(f"Preset '{preset_id}' não encontrado.")
        store["presets"][preset_id] = data
        save_presets(self.presets_path, store)
        return deepcopy(data)

    def calcular_torneio(
        self,
        jogadores: int,
        preset_id: str | None = None,
        valor_inscricao: float | None = None,
    ) -> dict[str, Any]:
        store = self._load()
        config = get_preset_config(store, preset_id)
        validar_jogadores(jogadores, config)
        if valor_inscricao is not None:
            validar_valor_inscricao(valor_inscricao)

        resultado = calcular(jogadores, config)
        total = sum(resultado["premios"])
        response: dict[str, Any] = {
            **resultado,
            "total_inscricoes": total,
        }
        if valor_inscricao is not None:
            casas = config["casas_decimais"]
            response["creditos"] = [
                round(p * valor_inscricao, casas) for p in resultado["premios"]
            ]
        return response

    def gerar_tabela(self, ate: int, preset_id: str | None = None) -> list[dict[str, Any]]:
        store = self._load()
        config = get_preset_config(store, preset_id)
        validar_limite_tabela(ate, config)
        min_j = config["min_jogadores"]
        return [calcular(n, config) for n in range(min_j, ate + 1)]

    def export_csv_bytes(
        self,
        ate: int,
        preset_id: str | None = None,
    ) -> tuple[bytes, str]:
        store = self._load()
        config = get_preset_config(store, preset_id)
        validar_limite_tabela(ate, config)
        min_j = config["min_jogadores"]
        resultados = [calcular(n, config) for n in range(min_j, ate + 1)]

        exports_dir = self._settings.resolved_exports_dir
        exports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"premiacao_{min_j}_a_{ate}_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.csv"
        filepath = exports_dir / filename

        max_premiados = max(r["premiados"] for r in resultados)
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";")
        cabecalho = ["Jogadores", "Premiados"]
        cabecalho.extend(f"{p}º Lugar" for p in range(1, max_premiados + 1))
        writer.writerow(cabecalho)
        for resultado in resultados:
            linha = [resultado["jogadores"], resultado["premiados"]]
            linha.extend(resultado["premios"])
            while len(linha) < max_premiados + 2:
                linha.append("")
            writer.writerow(linha)

        content = buffer.getvalue()
        raw = content.encode("utf-8-sig")
        filepath.write_bytes(raw)
        return raw, filename

    def exports_desatualizados(self) -> bool:
        """True if preset file is newer than any exported CSV."""
        exports_dir = self._settings.resolved_exports_dir
        if not exports_dir.exists():
            return False
        csvs = list(exports_dir.glob("premiacao_*.csv"))
        if not csvs:
            return False
        if not self.presets_path.exists():
            return False
        preset_mtime = self.presets_path.stat().st_mtime
        return any(preset_mtime > csv.stat().st_mtime for csv in csvs)
