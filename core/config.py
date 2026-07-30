"""Carregamento e persistência de ``config/settings.json``."""

from __future__ import annotations

import json
from typing import Any

from core.paths import CONFIG_DIR, SETTINGS_FILE
from core.validation import ConfigError, validar_config

# Usados apenas para gerar settings.json quando o arquivo não existe ou está inválido.
DEFAULT: dict[str, Any] = {
    "min_jogadores": 4,
    "min_premiados": 3,
    "max_premiados": 8,
    "crescimento": 4,
    "r": 0.72,
    "casas_decimais": 2,
}


def _escrever_settings(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _recriar_settings(motivo: str) -> dict[str, Any]:
    print(f"\n[config] {motivo}")
    print("[config] O arquivo config/settings.json será recriado com valores padrão.")

    if SETTINGS_FILE.exists():
        SETTINGS_FILE.unlink()

    config = DEFAULT.copy()
    _escrever_settings(config)
    print("[config] Arquivo recriado com sucesso.\n")
    return config.copy()


def load() -> dict[str, Any]:
    """
    Carrega configurações de ``settings.json``.

    O arquivo é a fonte da verdade. Valores default só entram em cena
    quando o arquivo não existe ou precisa ser recriado por erro de leitura.
    """
    if not SETTINGS_FILE.exists():
        print("\n[config] Arquivo config/settings.json não encontrado.")
        print("[config] Criando arquivo a partir dos valores padrão.\n")
        config = DEFAULT.copy()
        _escrever_settings(config)
        return config.copy()

    try:
        raw = SETTINGS_FILE.read_text(encoding="utf-8")
        config = json.loads(raw)
        validar_config(config)
        return config.copy()
    except (json.JSONDecodeError, ConfigError, OSError, TypeError) as exc:
        return _recriar_settings(f"Erro ao ler config/settings.json: {exc}")


def save(config: dict[str, Any]) -> bool:
    """
    Persiste configurações somente se houver alteração.

    Returns:
        True se o arquivo foi reescrito, False se nada mudou.
    """
    validar_config(config)

    novo_conteudo = json.dumps(config, indent=2, ensure_ascii=False) + "\n"

    if SETTINGS_FILE.exists():
        atual = SETTINGS_FILE.read_text(encoding="utf-8")
        if atual == novo_conteudo:
            return False

    _escrever_settings(config)
    return True
