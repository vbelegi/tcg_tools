"""Integration tests for premiacao API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_calcular():
    r = client.post(
        "/api/v1/premiacao/calcular",
        json={"jogadores": 24, "preset_id": "standard"},
    )
    assert r.status_code == 200
    data = r.json()
    assert sum(data["premios"]) == pytest.approx(24, abs=1e-9)


def test_tabela():
    r = client.get("/api/v1/premiacao/tabela?ate=8&preset_id=standard")
    assert r.status_code == 200
    linhas = r.json()["linhas"]
    assert len(linhas) == 5
    assert linhas[0]["jogadores"] == 4


def test_export():
    r = client.post(
        "/api/v1/premiacao/export",
        json={"ate": 8, "preset_id": "standard"},
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


def test_presets_exports_flag():
    r = client.get("/api/v1/premiacao/presets")
    assert r.status_code == 200
    assert "exports_desatualizados" in r.json()
