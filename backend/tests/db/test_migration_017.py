"""Migration 017 superadmin role seed."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text


def _cfg(url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_migration_017_promotes_admin_local(monkeypatch, tmp_path):
    db_file = tmp_path / "m017.db"
    url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path / "data"))

    from app.config import get_settings

    get_settings.cache_clear()
    command.upgrade(_cfg(url), "016")

    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (email, display_name, role, status, password_hash, "
                "marketing_opt_out, created_at, updated_at) "
                "VALUES ('admin@local', 'Admin', 'admin', 'active', 'x', 0, "
                "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO users (email, display_name, role, status, password_hash, "
                "marketing_opt_out, created_at, updated_at) "
                "VALUES ('other@example.com', 'Other', 'admin', 'active', 'x', 0, "
                "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
    engine.dispose()

    command.upgrade(_cfg(url), "017")

    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            roles = {
                row[0]: row[1]
                for row in conn.execute(text("SELECT email, role FROM users")).fetchall()
            }
        assert roles["admin@local"] == "superadmin"
        assert roles["other@example.com"] == "admin"
    finally:
        engine.dispose()
        get_settings.cache_clear()
