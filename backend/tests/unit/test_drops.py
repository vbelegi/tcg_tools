"""Unit tests for drop rules."""

from __future__ import annotations

import pytest

from app.core.torneios.drops import (
    DropError,
    apply_mid_round_drop,
    validate_drop_between_rounds,
    validate_drop_mid_round,
)


def test_mid_round_drop_bo3_gives_2_0_to_opponent():
    assert apply_mid_round_drop(0, 0, dropped_is_p1=True, best_of=3) == (0, 2)
    assert apply_mid_round_drop(1, 0, dropped_is_p1=False, best_of=3) == (2, 0)


def test_validate_mid_round_requires_active_round():
    with pytest.raises(DropError, match="Nenhuma rodada ativa"):
        validate_drop_mid_round("running", has_active_round=False)


def test_validate_between_rounds_rejects_active_round():
    with pytest.raises(DropError, match="Rodada ativa"):
        validate_drop_between_rounds("running", has_active_round=True)


def test_validate_between_rounds_allows_gap():
    validate_drop_between_rounds("running", has_active_round=False)
