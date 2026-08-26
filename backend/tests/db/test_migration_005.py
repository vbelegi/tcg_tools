"""Migration 005 platform users / FP."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def _cfg(url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_migration_005_platform_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "tcg.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path / "data"))
    from app.config import get_settings

    get_settings.cache_clear()
    command.upgrade(_cfg(url), "head")
    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert "invite_tokens" in tables
    assert "fourse_points_ledger" in tables
    cols_users = {c["name"] for c in inspect(engine).get_columns("users")}
    assert {"email", "display_name", "role", "status", "phone"}.issubset(cols_users)
    cols_players = {c["name"] for c in inspect(engine).get_columns("players")}
    assert {"attendance", "registration_source"}.issubset(cols_players)
    cols_events = {c["name"] for c in inspect(engine).get_columns("events")}
    assert {"source", "registration_open", "fp_n_at_start"}.issubset(cols_events)
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO users (email, display_name, role, status, password_hash, created_at, updated_at) "
                "VALUES ('a@b.com', 'A', 'player', 'incomplete', NULL, '2026-01-01', '2026-01-01')"
            )
        )
        conn.commit()
    engine.dispose()
    get_settings.cache_clear()
