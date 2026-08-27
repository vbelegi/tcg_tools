"""Initialize database via Alembic migrations."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.config import get_settings

logger = logging.getLogger(__name__)
_initialized = False


def init_db() -> None:
    """Apply Alembic migrations on startup (idempotent)."""
    global _initialized
    if _initialized:
        return

    settings = get_settings()
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.resolved_database_url)

    engine = create_engine(settings.resolved_database_url)
    try:
        tables = set(inspect(engine).get_table_names())
        if not tables:
            command.upgrade(cfg, "head")
        elif "alembic_version" not in tables and "events" in tables:
            logger.info("DB legado (create_all); carimbando 001 e aplicando migrações pendentes.")
            command.stamp(cfg, "001")
            command.upgrade(cfg, "head")
        elif "alembic_version" in tables and "events" in tables:
            with engine.connect() as conn:
                version_rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
            if not version_rows:
                logger.info("alembic_version vazio com schema existente; carimbando 001.")
                command.stamp(cfg, "001")
            command.upgrade(cfg, "head")
        elif "alembic_version" in tables:
            command.upgrade(cfg, "head")
        else:
            command.upgrade(cfg, "head")

        # Garantir coluna scores_submitted em DBs legados sem alembic
        table_names = set(inspect(engine).get_table_names())
        if "matches" in table_names:
            cols = {c["name"] for c in inspect(engine).get_columns("matches")}
            if "scores_submitted" not in cols:
                dialect = engine.dialect.name
                if dialect == "sqlite":
                    ddl = "ALTER TABLE matches ADD COLUMN scores_submitted BOOLEAN NOT NULL DEFAULT 0"
                else:
                    ddl = (
                        "ALTER TABLE matches ADD COLUMN scores_submitted "
                        "BOOLEAN NOT NULL DEFAULT FALSE"
                    )
                with engine.connect() as conn:
                    conn.execute(text(ddl))
                    conn.commit()
    except Exception as exc:
        logger.error("Alembic upgrade failed: %s", exc)
        raise
    finally:
        engine.dispose()
    _initialized = True
