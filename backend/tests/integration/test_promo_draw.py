"""Promotional action draw: one shot after end_date, CSV, player win/lose flags."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration.test_promo_actions_api import _create
from tests.integration.test_promo_enrollment import _issue, _verified_player


def _admin(client: TestClient) -> None:
    r = client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    assert r.status_code == 200, r.text


def _enroll(client: TestClient, db: Session, action_id: int, suffix: str) -> dict:
    _admin(client)
    raw, _ = _issue(client, action_id)
    player = _verified_player(db, client, suffix)
    assert client.get(f"/api/v1/acoes/enroll/{raw}").json()["reason"] == "ok"
    _admin(client)
    return player


def _close(client: TestClient, action_id: int) -> None:
    r = client.patch(
        f"/api/v1/acoes/{action_id}",
        json={
            "start_date": (date.today() - timedelta(days=10)).isoformat(),
            "end_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )
    assert r.status_code == 200, r.text


def test_draw_before_end_is_rejected(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    _enroll(api_client, db_session, action["id"], "1501")
    r = api_client.post(
        f"/api/v1/acoes/{action['id']}/draw",
        json={"mode": "direct", "winner_count": 1},
    )
    assert r.status_code == 400
    assert "término" in r.json()["detail"]


def test_draw_without_confirmed_participants(api_client: TestClient):
    action = _create(api_client)
    _close(api_client, action["id"])
    r = api_client.post(
        f"/api/v1/acoes/{action['id']}/draw",
        json={"mode": "direct", "winner_count": 1},
    )
    assert r.status_code == 400
    assert "confirmados" in r.json()["detail"]


def test_direct_draw_once_and_csv(
    api_client: TestClient, db_session: Session
):
    action = _create(api_client)
    api_client.post(f"/api/v1/acoes/{action['id']}/publish")
    first = _enroll(api_client, db_session, action["id"], "1502")
    second = _enroll(api_client, db_session, action["id"], "1503")
    _close(api_client, action["id"])

    drawn = api_client.post(
        f"/api/v1/acoes/{action['id']}/draw",
        json={"mode": "direct", "winner_count": 1},
    )
    assert drawn.status_code == 200, drawn.text
    body = drawn.json()
    assert body["mode"] == "direct"
    assert body["winner_count"] == 1
    assert len(body["winners"]) == 1
    winner_id = body["winners"][0]["user_id"]
    assert winner_id in {first["id"], second["id"]}
    assert "email" not in body["winners"][0]

    again = api_client.post(
        f"/api/v1/acoes/{action['id']}/draw",
        json={"mode": "direct", "winner_count": 1},
    )
    assert again.status_code == 409
    assert "já foi realizado" in again.json()["detail"]

    csv_resp = api_client.get(f"/api/v1/acoes/{action['id']}/winners.csv")
    assert csv_resp.status_code == 200
    text = csv_resp.text
    assert "nome_exibicao" in text
    assert "email" in text.splitlines()[0]
    assert "telefone" in text
    assert "enroll.1502@example.com" in text or "enroll.1503@example.com" in text

    loser = second if winner_id == first["id"] else first
    winner = first if winner_id == first["id"] else second
    api_client.post(
        "/api/v1/auth/login",
        json={"email": winner["email"], "password": "password1234"},
    )
    win_detail = api_client.get(f"/api/v1/acoes/{action['id']}").json()
    assert win_detail["draw_done"] is True
    assert win_detail["i_won"] is True
    assert "winners" not in win_detail
    assert "draw" not in win_detail

    api_client.post(
        "/api/v1/auth/login",
        json={"email": loser["email"], "password": "password1234"},
    )
    lose_detail = api_client.get(f"/api/v1/acoes/{action['id']}").json()
    assert lose_detail["draw_done"] is True
    assert lose_detail["i_won"] is False

    api_client.post("/api/v1/auth/logout")
    public = api_client.get(f"/api/v1/acoes/{action['id']}").json()
    assert "draw_done" not in public
    assert "i_won" not in public
    assert api_client.get(f"/api/v1/acoes/{action['id']}/winners").status_code == 401


def test_chained_draw_persists_order(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    first = _enroll(api_client, db_session, action["id"], "1504")
    second = _enroll(api_client, db_session, action["id"], "1505")
    _close(api_client, action["id"])

    r = api_client.post(
        f"/api/v1/acoes/{action['id']}/draw",
        json={"mode": "chained", "winner_user_ids": [second["id"], first["id"]]},
    )
    assert r.status_code == 200, r.text
    ids = [w["user_id"] for w in r.json()["winners"]]
    assert ids == [second["id"], first["id"]]

    listed = api_client.get(f"/api/v1/acoes/{action['id']}/winners")
    assert listed.status_code == 200
    assert [w["user_id"] for w in listed.json()["winners"]] == ids


def test_player_cannot_read_winners(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    player = _enroll(api_client, db_session, action["id"], "1506")
    _close(api_client, action["id"])
    assert (
        api_client.post(
            f"/api/v1/acoes/{action['id']}/draw",
            json={"mode": "direct", "winner_count": 1},
        ).status_code
        == 200
    )
    api_client.post(
        "/api/v1/auth/login",
        json={"email": player["email"], "password": "password1234"},
    )
    assert api_client.get(f"/api/v1/acoes/{action['id']}/winners").status_code == 403
    assert api_client.get(f"/api/v1/acoes/{action['id']}/winners.csv").status_code == 403
