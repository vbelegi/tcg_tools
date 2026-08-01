"""Tests for path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import paths
from app.config import Settings, get_settings


def test_default_data_subdirs():
    assert paths.default_exports_dir() == paths.default_data_dir() / "exports"
    assert paths.default_logs_dir() == paths.default_data_dir() / "logs"


def test_settings_resolved_dirs_use_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.resolved_exports_dir == tmp_path / "exports"
    assert settings.resolved_logs_dir == tmp_path / "logs"
    assert settings.resolved_presets_file == tmp_path / "premiacao_presets.json"
    get_settings.cache_clear()


def test_ensure_dirs_seeds_presets_from_bundled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    settings = Settings()
    settings.ensure_dirs()
    assert settings.resolved_presets_file.is_file()
    bundled = paths.bundled_presets_file()
    if bundled.is_file():
        assert settings.resolved_presets_file.read_text(encoding="utf-8") == bundled.read_text(
            encoding="utf-8"
        )
    get_settings.cache_clear()


def test_settings_explicit_exports_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    custom = tmp_path / "custom_exports"
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("TCGTOOLS_EXPORTS_DIR", str(custom))
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.resolved_exports_dir == custom
    get_settings.cache_clear()
