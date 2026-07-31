"""Premiacao service unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.premiacao_service import PremiacaoService


@pytest.fixture
def premiacao_svc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("TCGTOOLS_EXPORTS_DIR", str(tmp_path / "exports"))
    from app.config import get_settings

    get_settings.cache_clear()
    return PremiacaoService()


def test_calcular_service(premiacao_svc: PremiacaoService):
    result = premiacao_svc.calcular_torneio(16, preset_id="standard")
    assert sum(result["premios"]) == pytest.approx(16, abs=1e-9)


def test_tabela_service(premiacao_svc: PremiacaoService):
    rows = premiacao_svc.gerar_tabela(8, preset_id="standard")
    assert len(rows) >= 1
    assert rows[0]["jogadores"] == 4


def test_list_presets(premiacao_svc: PremiacaoService):
    data = premiacao_svc.list_presets()
    assert "presets" in data
    assert "standard" in data["presets"]
