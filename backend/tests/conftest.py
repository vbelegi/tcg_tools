"""Shared pytest fixtures aligned with production (Alembic migrations)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.session import get_db
from app.main import app
from app.services.torneio_service import TorneioService


def _alembic_config(db_url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


@pytest.fixture
def alembic_db_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Temp SQLite DB migrated via Alembic (same path as production)."""
    db_path = tmp_path / "tcg_tools.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    command.upgrade(_alembic_config(url), "head")
    return url


@pytest.fixture
def db_session(alembic_db_url: str) -> Generator[Session, None, None]:
    from sqlalchemy import create_engine

    engine = create_engine(
        alembic_db_url,
        connect_args={"check_same_thread": False},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def torneio_service(db_session: Session) -> TorneioService:
    return TorneioService(db_session)


@pytest.fixture
def swiss_event(torneio_service: TorneioService):
    """Draft Swiss event with 4 players."""
    event = torneio_service.create_event(
        name="Swiss Test",
        event_date=date.today(),
        format="swiss",
        max_rounds=2,
        entry_fee=10.0,
        best_of=3,
        premiacao_preset_id="standard",
    )
    for name in ("A", "B", "C", "D"):
        torneio_service.add_player(event.id, name)
    return event


def score_all_matches(
    svc: TorneioService,
    event_id: int,
    round_number: int,
    scores: list[tuple[int, int]] | None = None,
    *,
    default: tuple[int, int] = (2, 0),
) -> None:
    """Score non-bye matches. Uses `default` for every match when scores is omitted."""
    rnd = svc.get_round(event_id, round_number)
    non_bye = [m for m in rnd["matches"] if not m["is_bye"]]
    if scores is None:
        scores = [default] * len(non_bye)
    if len(scores) < len(non_bye):
        scores = list(scores) + [default] * (len(non_bye) - len(scores))
    for m, (s1, s2) in zip(non_bye, scores):
        svc.update_match(event_id, m["id"], s1, s2)


@pytest.fixture
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI client with real DB session (Alembic-migrated)."""

    def _override_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    yield TestClient(app)
    app.dependency_overrides.clear()
