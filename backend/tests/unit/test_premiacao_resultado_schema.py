"""Premiacao resultado schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.premiacao_resultado import PremiacaoResultado, validate_premiacao_resultado


def test_se_schema_v2_validates():
    data = {
        "schema_version": 2,
        "jogadores": 4,
        "premiados": 3,
        "premios": [2.0, 1.0, 1.0],
        "entry_fee": 35.0,
        "creditos": [70.0, 35.0, 17.5],
        "total_creditos": 140.0,
        "standings_snapshot": [],
        "bands": [
            {
                "label": "1º",
                "pool": 2.0,
                "tier_indices": [0],
                "player_count": 1,
                "payout_per_player": 2.0,
            }
        ],
        "player_payouts": [
            {"player_id": 1, "name": "A", "band_label": "1º", "payout": 2.0},
            {"player_id": 2, "name": "B", "band_label": "2º", "payout": 1.0},
            {"player_id": 3, "name": "C", "band_label": "3–4", "payout": 0.5},
        ],
    }
    model = validate_premiacao_resultado(data)
    assert model.schema_version == 2
    assert model.total_creditos == 140.0


def test_creditos_length_must_match_player_payouts():
    data = {
        "schema_version": 2,
        "jogadores": 4,
        "premiados": 3,
        "premios": [2.0, 1.0, 1.0],
        "entry_fee": 10.0,
        "creditos": [20.0],
        "total_creditos": 40.0,
        "standings_snapshot": [],
        "player_payouts": [
            {"player_id": 1, "name": "A", "band_label": "1º", "payout": 2.0},
            {"player_id": 2, "name": "B", "band_label": "2º", "payout": 1.0},
        ],
    }
    with pytest.raises(ValidationError):
        PremiacaoResultado.model_validate(data)


def test_swiss_schema_v1_minimal():
    data = {
        "schema_version": 1,
        "jogadores": 4,
        "premiados": 3,
        "premios": [2.0, 1.0, 1.0],
        "entry_fee": 0,
        "creditos": None,
        "total_creditos": None,
        "standings_snapshot": [{"rank": 1}],
    }
    assert validate_premiacao_resultado(data).schema_version == 1
