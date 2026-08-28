"""Public profile aggregation and FP visibility."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import register_player
from tests.conftest import score_all_matches
from app.services.torneio_service import TorneioService


def test_profile_hides_fp_from_strangers(api_client: TestClient, db_session: Session):
    player = register_player(
        db_session,
        display_name="Perfil Jogador",
        email="perfil.j@example.com",
        phone="+5511988880001",
        password="abcdef",
        birth_date=date(1998, 1, 15),
    )

    create = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "Profile Swiss",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 1,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
            "tcg_game_id": 1,
        },
    )
    assert create.status_code == 200, create.text
    eid = create.json()["id"]
    assert (
        api_client.post(
            f"/api/v1/torneios/{eid}/jogadores",
            json={"name": player.display_name, "user_id": player.id},
        ).status_code
        == 200
    )
    for name in ("B", "C", "D"):
        assert (
            api_client.post(
                f"/api/v1/torneios/{eid}/jogadores",
                json={
                    "name": name,
                    "create_account": True,
                    "email": f"{name.lower()}.prof.{eid}@api.test",
                    "phone": f"+55115{eid % 10000:04d}{ord(name):04d}",
                },
            ).status_code
            == 200
        )
    assert api_client.post(f"/api/v1/torneios/{eid}/iniciar").status_code == 200
    svc = TorneioService(db_session)
    score_all_matches(svc, eid, 1)
    assert api_client.post(f"/api/v1/torneios/{eid}/avancar").status_code == 200
    assert api_client.post(f"/api/v1/torneios/{eid}/finalizar").status_code == 200

    # admin (api_client session) sees FP
    as_admin = api_client.get(f"/api/v1/jogadores/{player.id}/perfil")
    assert as_admin.status_code == 200
    body = as_admin.json()
    assert body["fourse_points_visible"] is True
    assert body["fourse_points"] is not None
    assert body["stats"]["tournaments"] == 1
    assert body["history"][0]["tcg_game"]["id"] == 1
    assert "badge_games" in body
    assert body["insights"]

    api_client.post("/api/v1/auth/logout")
    guest = api_client.get(f"/api/v1/jogadores/{player.id}/perfil")
    assert guest.status_code == 200
    guest_body = guest.json()
    assert guest_body["fourse_points_visible"] is False
    assert guest_body["fourse_points"] is None
    assert guest_body["fp_by_game"] == []
    assert guest_body["fp_by_month"] == []
    assert guest_body["ranking_position"] is None
    assert "fp_earned" not in guest_body["history"][0]
    assert guest_body["history"]

    # owner sees FP
    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "perfil.j@example.com", "password": "abcdef"},
    )
    assert login.status_code == 200
    own = api_client.get(f"/api/v1/jogadores/{player.id}/perfil")
    assert own.status_code == 200
    assert own.json()["fourse_points_visible"] is True
    assert own.json()["can_edit"] is True


def test_update_display_name_and_avatar(api_client: TestClient, db_session: Session):
    from io import BytesIO

    from PIL import Image

    player = register_player(
        db_session,
        display_name="Antes",
        email="avatar.u@example.com",
        phone="+5511988880002",
        password="abcdef",
        birth_date=date(1990, 5, 5),
    )
    api_client.post("/api/v1/auth/logout")
    assert (
        api_client.post(
            "/api/v1/auth/login",
            json={"email": "avatar.u@example.com", "password": "abcdef"},
        ).status_code
        == 200
    )

    patched = api_client.patch("/api/v1/auth/me", json={"display_name": "Depois"})
    assert patched.status_code == 200
    assert patched.json()["display_name"] == "Depois"

    buf = BytesIO()
    Image.new("RGB", (80, 80), color=(10, 20, 30)).save(buf, format="PNG")
    upload = api_client.post(
        "/api/v1/auth/me/avatar",
        files={"file": ("face.png", buf.getvalue(), "image/png")},
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["avatar_url"]
    assert upload.json()["avatar_url"].startswith("/api/v1/media/avatars/")

    profile = api_client.get(f"/api/v1/jogadores/{player.id}/perfil")
    assert profile.json()["avatar_url"] == upload.json()["avatar_url"]
    assert profile.json()["display_name"] == "Depois"

    avatar_get = api_client.get(f"/api/v1/media/avatars/{player.id}")
    assert avatar_get.status_code == 200
    assert avatar_get.headers["content-type"].startswith("image/webp")
    assert len(avatar_get.content) > 100


def test_create_torneio_requires_tcg(api_client: TestClient):
    r = api_client.post(
        "/api/v1/torneios",
        json={
            "name": "No TCG",
            "event_date": date.today().isoformat(),
            "format": "swiss",
            "max_rounds": 2,
            "entry_fee": 10,
            "best_of": 3,
            "premiacao_preset_id": "standard",
        },
    )
    assert r.status_code == 422


def test_admin_has_native_profile(api_client: TestClient, db_session: Session):
    from app.core.auth import get_admin

    admin = get_admin(db_session)
    assert admin is not None
    r = api_client.get(f"/api/v1/jogadores/{admin.id}/perfil")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == admin.id
    assert body["display_name"]
    assert body["can_edit"] is True
    assert body["fourse_points_visible"] is True


def test_public_player_search(api_client: TestClient, db_session: Session):
    register_player(
        db_session,
        display_name="Busca Alpha",
        email="busca.alpha@example.com",
        phone="+5511988880011",
        password="abcdef",
        birth_date=date(1994, 2, 2),
    )
    register_player(
        db_session,
        display_name="Outro Nome",
        email="outro.nome@example.com",
        phone="+5511988880012",
        password="abcdef",
        birth_date=date(1993, 3, 3),
    )
    api_client.post("/api/v1/auth/logout")
    hit = api_client.get("/api/v1/jogadores/buscar", params={"q": "Alpha"})
    assert hit.status_code == 200
    body = hit.json()
    assert len(body) == 1
    assert body[0]["display_name"] == "Busca Alpha"
    assert set(body[0].keys()) == {"id", "display_name", "avatar_url"}
    assert "email" not in body[0]


def test_incomplete_profile_is_public(api_client: TestClient, db_session: Session):
    from app.core.auth import create_incomplete_user

    user = create_incomplete_user(
        db_session,
        display_name="Incompleto Público",
        email="incomp.pub@example.com",
        phone="+5511988880099",
    )
    assert user.status == "incomplete"

    api_client.post("/api/v1/auth/logout")
    guest = api_client.get(f"/api/v1/jogadores/{user.id}/perfil")
    assert guest.status_code == 200, guest.text
    body = guest.json()
    assert body["id"] == user.id
    assert body["display_name"] == "Incompleto Público"
    assert body["status"] == "incomplete"
    assert body["fourse_points_visible"] is False
    assert body["can_edit"] is False
    assert "email" not in body
    assert "phone" not in body

    search = api_client.get("/api/v1/jogadores/buscar", params={"q": "Incompleto"})
    assert search.status_code == 200
    hits = search.json()
    assert any(h["id"] == user.id for h in hits)
