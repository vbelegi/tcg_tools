"""Migration 013 email verification."""

from __future__ import annotations

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect


def test_migration_013_email_verification(monkeypatch, tmp_path):
    db_file = tmp_path / "m013.db"
    url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path / "data"))

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "013")

    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        insp = inspect(db.bind)
        tables = insp.get_table_names()
        assert "email_verification_tokens" in tables
        cols = {c["name"] for c in insp.get_columns("users")}
        assert "email_verified_at" in cols
    finally:
        db.close()
