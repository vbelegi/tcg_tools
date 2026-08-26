"""Integration: presets writable under data_dir (installed layout simulation)."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import paths
from app.config import get_settings
from app.core.auth import upsert_admin_password
from app.db.session import get_db
from app.main import app


def _alembic_config(db_url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


@pytest.fixture
def installed_layout_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Generator[tuple[TestClient, Path, Path], None, None]:
    """Simulate per-user install: bundled presets read-only, writes go to data_dir."""
    data_dir = tmp_path / "AppData" / "TCGTools"
    data_dir.mkdir(parents=True)
    db_path = data_dir / "tcg_tools.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(data_dir))
    monkeypatch.setenv("TCGTOOLS_DATABASE_URL", url)
    get_settings.cache_clear()
    command.upgrade(_alembic_config(url), "head")

    settings = get_settings()
    presets_path = settings.resolved_presets_file
    bundled = paths.bundled_presets_file()

    assert bundled.is_file(), "bundled presets required for install simulation"
    assert presets_path.is_file()
    assert presets_path.parent == data_dir
    assert presets_path.read_text(encoding="utf-8") == bundled.read_text(encoding="utf-8")

    engine = create_engine(url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session: Session = SessionLocal()
    upsert_admin_password(session, "testpass")

    def _override_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)
    r = client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass"})
    assert r.status_code == 200, r.text

    try:
        yield client, presets_path, bundled
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()
        get_settings.cache_clear()


def test_presets_put_writes_to_data_dir_not_bundled(installed_layout_client):
    client, presets_path, bundled = installed_layout_client
    bundled_before = bundled.read_text(encoding="utf-8")

    listed = client.get("/api/v1/premiacao/presets")
    assert listed.status_code == 200
    mtime = listed.json().get("presets_updated_at")

    body = client.get("/api/v1/premiacao/presets/standard").json()
    body["label"] = "Preset alterado no teste install layout"
    headers = {}
    if mtime is not None:
        headers["X-Presets-Mtime"] = str(mtime)

    updated = client.put(
        "/api/v1/premiacao/presets/standard",
        json=body,
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["label"] == "Preset alterado no teste install layout"

    on_disk = json.loads(presets_path.read_text(encoding="utf-8"))
    assert on_disk["presets"]["standard"]["label"] == "Preset alterado no teste install layout"
    assert bundled.read_text(encoding="utf-8") == bundled_before
