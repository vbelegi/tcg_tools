"""Unit tests for presets."""

import json
import tempfile
from pathlib import Path

import pytest

from app.core.premiacao.presets import (
    DEFAULT_STORE,
    load_presets,
    migrate_legacy_settings,
    save_presets,
)


def test_migrate_legacy_settings(tmp_path):
    legacy = tmp_path / "settings.json"
    legacy.write_text(
        json.dumps(
            {
                "min_jogadores": 4,
                "min_premiados": 3,
                "max_premiados": 8,
                "crescimento": 3,
                "r": 0.72,
                "casas_decimais": 2,
            }
        ),
        encoding="utf-8",
    )
    result = migrate_legacy_settings(legacy)
    assert result is not None
    assert "default" in result["presets"]
    assert result["presets"]["default"]["crescimento"] == 3


def test_load_save_presets(tmp_path):
    path = tmp_path / "presets.json"
    store = load_presets(path)
    assert store["default_preset"] == DEFAULT_STORE["default_preset"]
    store["presets"]["standard"]["crescimento"] = 3
    assert save_presets(path, store) is True
    assert save_presets(path, store) is False
    reloaded = load_presets(path)
    assert reloaded["presets"]["standard"]["crescimento"] == 3
