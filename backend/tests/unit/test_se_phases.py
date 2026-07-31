"""Unit tests for SE phases."""

from __future__ import annotations

from app.core.torneios.se_phases import (
    audit_se_bo_config,
    normalize_se_bo_config,
    resolve_best_of,
    rounds_from_final,
)


def test_rounds_from_final():
    assert rounds_from_final(3, 3) == 1
    assert rounds_from_final(2, 3) == 2
    assert rounds_from_final(1, 3) == 3


def test_resolve_best_of_legacy():
    assert resolve_best_of(1, 3, None, 3) == 3


def test_resolve_best_of_config():
    config = {1: 5, 2: 3, 3: 1}
    assert resolve_best_of(3, 3, config, 3) == 5
    assert resolve_best_of(2, 3, config, 3) == 3
    assert resolve_best_of(1, 3, config, 3) == 1


def test_normalize_se_bo_config():
    assert normalize_se_bo_config({"1": 3, "2": 1}) == {1: 3, 2: 1}


def test_audit_se_bo_config_prunes_orphan_phases():
    pruned, warnings = audit_se_bo_config({1: 5, 2: 3, 4: 1}, max_rounds=2)
    assert pruned == {1: 5, 2: 3}
    assert len(warnings) == 1
    assert "rounds_from_final=4" in warnings[0]


def test_bronze_inherits_final_bo():
    config = {1: 5, 2: 3}
    assert resolve_best_of(2, 2, config, 1) == 5
