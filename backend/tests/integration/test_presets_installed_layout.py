"""Integration: presets writable under data_dir (installed layout simulation)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import paths
from app.config import get_settings
from app.main import app


@pytest.fixture
def installed_layout_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Simulate per-user install: bundled presets read-only, writes go to data_dir."""
    data_dir = tmp_path / "AppData" / "TCGTools"
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(data_dir))
    get_settings.cache_clear()
    settings = get_settings()
    presets_path = settings.resolved_presets_file
    bundled = paths.bundled_presets_file()

    assert bundled.is_file(), "bundled presets required for install simulation"
    assert presets_path.is_file()
    assert presets_path.parent == data_dir
    assert presets_path.read_text(encoding="utf-8") == bundled.read_text(encoding="utf-8")

    yield TestClient(app), presets_path, bundled
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
