"""Unit tests for CSV export."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.config import Settings
from app.services.premiacao_service import PremiacaoService


@pytest.fixture
def export_env(tmp_path: Path):
    presets = tmp_path / "presets.json"
    presets.write_text(
        """{
  "version": 1,
  "default_preset": "standard",
  "presets": {
    "standard": {
      "label": "Test",
      "min_jogadores": 4,
      "min_premiados": 3,
      "max_premiados": 8,
      "crescimento": 4,
      "r": 0.72,
      "casas_decimais": 2
    }
  }
}""",
        encoding="utf-8",
    )
    exports = tmp_path / "exports"
    exports.mkdir()
    settings = Settings(
        data_dir=tmp_path / "data",
        presets_file=presets,
        exports_dir=exports,
        logs_dir=tmp_path / "logs",
    )
    return settings, exports


def test_export_csv_writes_file(export_env):
    settings, exports_dir = export_env
    svc = PremiacaoService(settings=settings)
    content, filename = svc.export_csv_bytes(8, "standard")
    assert filename.startswith("premiacao_4_a_8_")
    assert b"Jogadores" in content
    written = exports_dir / filename
    assert written.exists()
    assert written.read_bytes().replace(b"\r\n", b"\n") == content.replace(b"\r\n", b"\n")


def test_export_csv_uses_tempfile_isolation(export_env):
    settings, exports_dir = export_env
    svc = PremiacaoService(settings=settings)
    with tempfile.TemporaryDirectory() as other:
        other_exports = Path(other)
        alt = Settings(
            data_dir=Path(other) / "data",
            presets_file=settings.presets_file,
            exports_dir=other_exports,
        )
        svc2 = PremiacaoService(settings=alt)
        svc2.export_csv_bytes(8, "standard")
        assert list(exports_dir.glob("*.csv")) == []
        assert len(list(other_exports.glob("*.csv"))) == 1
