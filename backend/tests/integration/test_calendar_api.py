"""Calendar feed and announcement CRUD."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from fastapi.testclient import TestClient

from tests.integration.test_promo_actions_api import _create


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
    assert "promo_actions" in body
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


def test_announcements_filter_by_title_and_date_range(api_client: TestClient):
    a = api_client.post(
        "/api/v1/calendar/announcements",
        json={"title": "Pré-release Magic", "event_date": "2026-09-10"},
    )
    b = api_client.post(
        "/api/v1/calendar/announcements",
        json={"title": "Mesa aberta Pokémon", "event_date": "2026-09-25"},
    )
    assert a.status_code == 201
    assert b.status_code == 201
    a_id = a.json()["id"]
    b_id = b.json()["id"]

    by_title = api_client.get("/api/v1/calendar/announcements", params={"q": "magic"}).json()
    assert [row["id"] for row in by_title] == [a_id]

    by_range = api_client.get(
        "/api/v1/calendar/announcements",
        params={"from": "2026-09-20", "to": "2026-09-30"},
    ).json()
    assert [row["id"] for row in by_range] == [b_id]

    both = api_client.get(
        "/api/v1/calendar/announcements",
        params={"from": "2026-09-01", "to": "2026-09-30", "q": "pré"},
    ).json()
    assert [row["id"] for row in both] == [a_id]

    today = date.today()
    last = monthrange(today.year, today.month)[1]
    start = date(today.year, today.month, last)
    if today.month == 12:
        next_year, next_month = today.year + 1, 1
    else:
        next_year, next_month = today.year, today.month + 1
    end = date(next_year, next_month, min(5, monthrange(next_year, next_month)[1]))

    action = _create(
        api_client,
        name="Faixa contínua",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
    )
    assert api_client.post(f"/api/v1/acoes/{action['id']}/publish").status_code == 200

    this_month = api_client.get(f"/api/v1/calendar?year={today.year}&month={today.month}").json()
    next_month = api_client.get(f"/api/v1/calendar?year={next_year}&month={next_month}").json()
    this_ids = [p["id"] for p in this_month["promo_actions"]]
    next_ids = [p["id"] for p in next_month["promo_actions"]]
    assert action["id"] in this_ids
    assert action["id"] in next_ids
    row = next(p for p in this_month["promo_actions"] if p["id"] == action["id"])
    assert row["name"] == "Faixa contínua"
    assert "participant_count" not in row
    assert row["type_label"] == "Sorteio de Direito de Compra Físico"


def test_draft_with_calendar_flag_is_absent_from_public_feed(api_client: TestClient):
    today = date.today()
    draft = _create(api_client, name="Rascunho no calendário", show_in_calendar=True)
    hidden = _create(api_client, name="Publicada sem calendário", show_in_calendar=False)
    assert api_client.post(f"/api/v1/acoes/{hidden['id']}/publish").status_code == 200

    feed = api_client.get(f"/api/v1/calendar?year={today.year}&month={today.month}").json()
    ids = [p["id"] for p in feed["promo_actions"]]
    assert draft["id"] not in ids
    assert hidden["id"] not in ids

    api_client.post("/api/v1/auth/logout")
    public = api_client.get(f"/api/v1/calendar?year={today.year}&month={today.month}").json()
    public_ids = [p["id"] for p in public["promo_actions"]]
    assert draft["id"] not in public_ids
    assert hidden["id"] not in public_ids

