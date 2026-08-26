"""init_db legacy and startup migration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, text

from app.config import get_settings
from app.db.init_db import init_db
from tests.conftest import _alembic_config


def test_init_db_on_empty_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "data" / "tcg_tools.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()

    import app.db.init_db as init_mod

    init_mod._initialized = False
    init_db()

    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert "events" in tables
    assert "alembic_version" in tables
    cols = {c["name"] for c in inspect(engine).get_columns("matches")}
    assert "scores_submitted" in cols
    assert "is_third_place" in cols
    event_cols = {c["name"] for c in inspect(engine).get_columns("events")}
    assert "third_place_match" in event_cols
    assert "se_bo_config" in event_cols
    engine.dispose()


def test_init_db_legacy_create_all_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Simulates DB created before Alembic (events table without alembic_version)."""
    db_path = tmp_path / "legacy.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    get_settings.cache_clear()

    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    event_date DATE NOT NULL,
                    format VARCHAR NOT NULL,
                    max_rounds INTEGER,
                    entry_fee FLOAT NOT NULL,
                    best_of INTEGER NOT NULL,
                    premiacao_preset JSON NOT NULL,
                    premiacao_resultado JSON,
                    status VARCHAR NOT NULL,
                    shuffle_seed INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE matches (
                    id INTEGER PRIMARY KEY,
                    round_id INTEGER NOT NULL,
                    player1_id INTEGER NOT NULL,
                    player2_id INTEGER,
                    winner_id INTEGER,
                    score_p1 INTEGER NOT NULL DEFAULT 0,
                    score_p2 INTEGER NOT NULL DEFAULT 0,
                    is_bye BOOLEAN NOT NULL DEFAULT 0,
                    is_walkover BOOLEAN NOT NULL DEFAULT 0,
                    had_rematch BOOLEAN NOT NULL DEFAULT 0
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE players (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    name VARCHAR NOT NULL,
                    user_id INTEGER,
                    seed INTEGER,
                    dropped_at DATETIME,
                    registration_order INTEGER NOT NULL,
                    decklist TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rounds (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    number INTEGER NOT NULL,
                    status VARCHAR NOT NULL
                )
                """
            )
        )
    engine.dispose()

    import app.db.init_db as init_mod

    init_mod._initialized = False
    init_db()

    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert "alembic_version" in tables
    cols = {c["name"] for c in inspect(engine).get_columns("matches")}
    assert "scores_submitted" in cols
    engine.dispose()
