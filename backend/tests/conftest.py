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


def create_se_event(
    svc: TorneioService,
    player_count: int,
    *,
    third_place_match: bool = False,
    se_bo_config: dict[str, int] | None = None,
    best_of: int = 1,
    entry_fee: float = 10.0,
    name: str = "SE Test",
):
    """Draft SE event with `player_count` registered players."""
    event = svc.create_event(
        name=name,
        event_date=date.today(),
        format="single_elimination",
        max_rounds=None,
        entry_fee=entry_fee,
        best_of=best_of,
        premiacao_preset_id="standard",
        third_place_match=third_place_match,
        se_bo_config=se_bo_config,
    )
    for i in range(player_count):
        svc.add_player(event.id, f"P{i + 1}")
    return event


def run_se_bracket(
    svc: TorneioService,
    event_id: int,
    *,
    default: tuple[int, int] = (2, 0),
) -> None:
    """Start SE event and play through until ready to finalize."""
    svc.start_event(event_id)
    while not svc.get_event(event_id)["can_finalize"]:
        ev = svc.get_event(event_id)
        if ev["between_rounds"]:
            svc.start_next_round(event_id)
            ev = svc.get_event(event_id)
        rnd = ev["current_round"]
        score_all_matches(svc, event_id, rnd, default=default)
        svc.complete_round(event_id)


@pytest.fixture
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI client with real DB session (Alembic-migrated) and admin login."""
    from app.core.auth import upsert_admin_password

    upsert_admin_password(db_session, "testpass")

    def _override_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "testpass"})
    assert r.status_code == 200, r.text
    yield client
    app.dependency_overrides.clear()
