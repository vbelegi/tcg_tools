"""Unit tests for build_premiacao_resultado."""

from __future__ import annotations

from app.core.premiacao.build_resultado import build_premiacao_resultado
from app.core.premiacao.presets import DEFAULT_PRESET
from app.core.torneios.models import BandMember


def _cfg():
    return {k: v for k, v in DEFAULT_PRESET.items() if k != "label"}


def test_total_creditos_equals_players_times_entry_fee():
    cfg = _cfg()
    members = [
        BandMember(1, "1º", name="A"),
        BandMember(2, "2º", name="B"),
        BandMember(3, "3–4", name="C"),
        BandMember(4, "3–4", name="D"),
    ]
    result = build_premiacao_resultado(
        format="single_elimination",
        n=4,
        config=cfg,
        third_place_match=False,
        members=members,
        standings_snapshot=[],
        entry_fee=35.0,
    )
    assert result["total_creditos"] == 140.0
    assert sum(result["creditos"]) == 140.0


def test_swiss_total_creditos():
    cfg = _cfg()
    members = [
        BandMember(1, "1º", name="A"),
        BandMember(2, "2º", name="B"),
        BandMember(3, "3º", name="C"),
    ]
    result = build_premiacao_resultado(
        format="swiss",
        n=4,
        config=cfg,
        third_place_match=False,
        members=members,
        standings_snapshot=[],
        entry_fee=10.0,
    )
    assert result["total_creditos"] == 40.0
    assert sum(result["creditos"]) == 40.0
