"""Unit tests for SE tier bands and payout."""

from __future__ import annotations

import pytest

from app.core.premiacao.se_payout import assign_se_band_payouts, preview_se_bands
from app.core.premiacao.validation import PayoutConservationError, validate_payout_conservation
from app.core.premiacao.presets import DEFAULT_PRESET
from app.core.torneios.models import BandMember
from app.core.torneios.se_bands import build_tier_bands, format_band_label


@pytest.fixture
def cfg():
    return {k: v for k, v in DEFAULT_PRESET.items() if k != "label"}


class TestTierBands:
    def test_format_band_label(self):
        assert format_band_label(1, 1) == "1º"
        assert format_band_label(3, 4) == "3–4"
        assert format_band_label(5, 8) == "5–8"

    def test_bands_without_bronze_8_players(self):
        bands = build_tier_bands(8, third_place_match=False)
        labels = [b.label for b in bands]
        assert labels[:3] == ["1º", "2º", "3–4"]
        assert "5–8" in labels

    def test_bands_with_bronze(self):
        bands = build_tier_bands(8, third_place_match=True)
        labels = [b.label for b in bands]
        assert labels[:4] == ["1º", "2º", "3º", "4º"]

    def test_bands_premiados_three_no_fourth_tier(self):
        bands = build_tier_bands(3, third_place_match=False)
        labels = [b.label for b in bands]
        assert labels == ["1º", "2º", "3–4"]


@pytest.mark.parametrize("n", [4, 8, 16, 32])
@pytest.mark.parametrize("third_place_match", [False, True])
def test_preview_conservation(n, third_place_match, cfg):
    bands = preview_se_bands(n, cfg, third_place_match)
    total_pool = sum(b.pool for b in bands)
    assert total_pool == pytest.approx(n, abs=1e-9)


class TestSePayout:
    def test_semi_drop_gets_full_pool(self, cfg):
        members = [
            BandMember(1, "1º", name="A"),
            BandMember(2, "2º", name="B"),
            BandMember(3, format_band_label(3, 4), name="C"),
        ]
        result = assign_se_band_payouts(8, cfg, members, third_place_match=False)
        c_payout = next(p for p in result.player_payouts if p.player_id == 3)
        band_34 = next(b for b in result.bands if b.label == format_band_label(3, 4))
        assert c_payout.payout == pytest.approx(band_34.pool, abs=1e-9)

    @pytest.mark.parametrize("n", [4, 8, 16, 32])
    def test_conservation_with_full_bands(self, n, cfg):
        from app.core.premiacao.calculator import calcular_premiados

        y = calcular_premiados(n, cfg)
        bands = build_tier_bands(y, False)
        members = []
        for band in bands:
            for _ in range(band.nominal_size):
                members.append(
                    BandMember(len(members) + 1, band.label, name=f"P{len(members)}")
                )
        result = assign_se_band_payouts(n, cfg, members[:n], False)
        validate_payout_conservation(
            n,
            [p.payout for p in result.player_payouts],
            cfg["casas_decimais"],
        )

    def test_conservation_error(self):
        with pytest.raises(PayoutConservationError):
            validate_payout_conservation(8, [1.0, 2.0], 2)

    def test_empty_band_pool_redistributed(self, cfg):
        members = [
            BandMember(1, "1º", name="A"),
            BandMember(2, "2º", name="B"),
        ]
        result = assign_se_band_payouts(8, cfg, members, third_place_match=False)
        validate_payout_conservation(
            8,
            [p.payout for p in result.player_payouts],
            cfg["casas_decimais"],
        )
