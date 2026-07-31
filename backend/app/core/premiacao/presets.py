"""Load/save premiacao presets JSON."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.core.premiacao.validation import ConfigError, validar_config

logger = logging.getLogger(__name__)

DEFAULT_PRESET: dict[str, Any] = {
    "label": "Standard semanal",
    "min_jogadores": 4,
    "min_premiados": 3,
    "max_premiados": 8,
    "crescimento": 4,
    "r": 0.72,
    "casas_decimais": 2,
}

DEFAULT_STORE: dict[str, Any] = {
    "version": 1,
    "default_preset": "standard",
    "presets": {
        "standard": deepcopy(DEFAULT_PRESET),
    },
}


def _validate_store(store: dict[str, Any]) -> None:
    if not isinstance(store, dict):
        raise ConfigError("Arquivo de presets deve ser um objeto JSON.")
    if "presets" not in store or not isinstance(store["presets"], dict):
        raise ConfigError("Campo 'presets' ausente ou inválido.")
    if not store["presets"]:
        raise ConfigError("Deve existir ao menos um preset.")
    default_id = store.get("default_preset")
    if default_id and default_id not in store["presets"]:
        raise ConfigError(f"default_preset '{default_id}' não encontrado.")
    for preset_id, preset in store["presets"].items():
        if not isinstance(preset, dict):
            raise ConfigError(f"Preset '{preset_id}' inválido.")
        validar_config(preset)


def migrate_legacy_settings(legacy_path: Path) -> dict[str, Any] | None:
    """Converte config/settings.json legado para um preset 'default'."""
    if not legacy_path.exists():
        return None
    try:
        raw = legacy_path.read_text(encoding="utf-8")
        config = json.loads(raw)
        validar_config(config)
        label = config.pop("label", None) if "label" in config else None
        preset = {**DEFAULT_PRESET, **config}
        if label:
            preset["label"] = label
        else:
            preset["label"] = "Padrão (migrado)"
        return {
            "version": 1,
            "default_preset": "default",
            "presets": {"default": preset},
        }
    except (json.JSONDecodeError, ConfigError, OSError, TypeError) as exc:
        logger.warning("Falha ao migrar settings legado: %s", exc)
        return None


def load_presets(path: Path, legacy_path: Path | None = None) -> dict[str, Any]:
    """Carrega presets; cria arquivo padrão se não existir."""
    if not path.exists():
        store = deepcopy(DEFAULT_STORE)
        if legacy_path:
            migrated = migrate_legacy_settings(legacy_path)
            if migrated:
                store = migrated
        save_presets(path, store)
        return deepcopy(store)

    try:
        raw = path.read_text(encoding="utf-8")
        store = json.loads(raw)
        _validate_store(store)
        return deepcopy(store)
    except (json.JSONDecodeError, ConfigError, OSError, TypeError) as exc:
        logger.warning("Presets inválidos, recriando: %s", exc)
        store = deepcopy(DEFAULT_STORE)
        save_presets(path, store)
        return deepcopy(store)


def save_presets(path: Path, store: dict[str, Any]) -> bool:
    """Persiste presets se houver alteração."""
    _validate_store(store)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(store, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def get_preset_config(store: dict[str, Any], preset_id: str | None = None) -> dict[str, Any]:
    """Retorna config de um preset (sem label)."""
    pid = preset_id or store.get("default_preset", "standard")
    presets = store["presets"]
    if pid not in presets:
        raise ConfigError(f"Preset '{pid}' não encontrado.")
    preset = deepcopy(presets[pid])
    preset.pop("label", None)
    return preset
