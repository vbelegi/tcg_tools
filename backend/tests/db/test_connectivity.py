"""Alembic connectivity and migration tests."""

from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import get_settings
from tests.conftest import _alembic_config


@pytest.fixture
def alembic_cfg(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Config:
    db_path = tmp_path / "migrate.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    get_settings.cache_clear()
    return _alembic_config(url)


def test_alembic_upgrade_and_downgrade(alembic_cfg: Config):
    command.upgrade(alembic_cfg, "head")
    url = get_settings().resolved_database_url
    engine = create_engine(url)
    tables = inspect(engine).get_table_names()
    assert {"events", "players", "rounds", "matches"}.issubset(set(tables))
    engine.dispose()

    command.downgrade(alembic_cfg, "base")
    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert "events" not in tables
    assert "players" not in tables
    assert "rounds" not in tables
    assert "matches" not in tables
    engine.dispose()
