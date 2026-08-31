"""Calendar feed and announcement CRUD."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient


def test_calendar_month_includes_tournaments_and_announcements(api_client: TestClient):
    today = date.today()
    create = api_client.post(
        "/api/v1/calendar/announcements",
        json={
            "title": "Pré-release",
            "event_date": today.isoformat(),
            "description": "Venha jogar",
            "start_time": "14:00",
            "location": "Loja",
        },
    )
    assert create.status_code == 201
    ann_id = create.json()["id"]

    r = api_client.get(f"/api/v1/calendar?year={today.year}&month={today.month}")
    assert r.status_code == 200
    body = r.json()
    assert "tournaments" in body
    assert "announcements" in body
    ids = [a["id"] for a in body["announcements"]]
    assert ann_id in ids


def test_announcement_crud(api_client: TestClient):
    today = date.today()
    create = api_client.post(
        "/api/v1/calendar/announcements",
        json={
            "title": "Mesa aberta",
            "event_date": today.isoformat(),
            "start_time": "19:30",
            "location": "Sala 2",
        },
    )
    assert create.status_code == 201
    ann_id = create.json()["id"]

    listed = api_client.get(
        f"/api/v1/calendar/announcements?year={today.year}&month={today.month}",
    )
    assert listed.status_code == 200
    assert any(a["id"] == ann_id for a in listed.json())

    patch = api_client.patch(
        f"/api/v1/calendar/announcements/{ann_id}",
        json={"title": "Mesa aberta (atualizado)", "location": "Sala 1"},
    )
    assert patch.status_code == 200
    assert patch.json()["title"] == "Mesa aberta (atualizado)"
    assert patch.json()["location"] == "Sala 1"

    delete = api_client.delete(f"/api/v1/calendar/announcements/{ann_id}")
    assert delete.status_code == 204

    gone = api_client.get(f"/api/v1/calendar/announcements?year={today.year}&month={today.month}")
    assert all(a["id"] != ann_id for a in gone.json())


def test_invalid_announcement_time(api_client: TestClient):
    r = api_client.post(
        "/api/v1/calendar/announcements",
        json={
            "title": "Horário ruim",
            "event_date": date.today().isoformat(),
            "start_time": "25:00",
        },
    )
    assert r.status_code == 422
