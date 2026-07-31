"""Migration 003 tests (via Alembic fixture aligned with production)."""

from __future__ import annotations

from alembic import command
from sqlalchemy import create_engine, inspect

from tests.conftest import _alembic_config


def test_migration_003_columns_present(alembic_db_url: str):
    engine = create_engine(alembic_db_url)
    event_cols = {c["name"] for c in inspect(engine).get_columns("events")}
    match_cols = {c["name"] for c in inspect(engine).get_columns("matches")}
    engine.dispose()
    assert {"third_place_match", "se_bo_config"}.issubset(event_cols)
    assert {"is_third_place", "best_of"}.issubset(match_cols)


def test_migration_003_downgrade_removes_se_columns(alembic_db_url: str):
    cfg = _alembic_config(alembic_db_url)
    command.downgrade(cfg, "002")
    engine = create_engine(alembic_db_url)
    event_cols = {c["name"] for c in inspect(engine).get_columns("events")}
    engine.dispose()
    assert "third_place_match" not in event_cols
