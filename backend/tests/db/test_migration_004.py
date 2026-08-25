"""Migration 004 auth tables."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def _cfg(url: str) -> Config:
    backend = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_migration_004_auth_tables(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path / "data"))
    from app.config import get_settings

    get_settings.cache_clear()
    command.upgrade(_cfg(url), "head")
    eng = create_engine(url)
    tables = inspect(eng).get_table_names()
    assert "users" in tables
    assert "sessions" in tables
    eng.dispose()
