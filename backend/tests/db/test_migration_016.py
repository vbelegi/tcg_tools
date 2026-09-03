"""Migration 016 contact change."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def _cfg(url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_migration_016_contact_change(monkeypatch, tmp_path):
    db_file = tmp_path / "m016.db"
    url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path / "data"))

    from app.config import get_settings

    get_settings.cache_clear()
    command.upgrade(_cfg(url), "head")

    engine = create_engine(url)
    try:
        insp = inspect(engine)
        assert "email_change_tokens" in insp.get_table_names()
        cols = {c["name"] for c in insp.get_columns("users")}
        assert "phone_verified_at" in cols
        assert "pending_phone" in cols
        token_cols = {c["name"] for c in insp.get_columns("email_change_tokens")}
        assert {"token", "user_id", "new_email", "created_at", "expires_at", "used_at"} <= token_cols
    finally:
        engine.dispose()
        get_settings.cache_clear()
