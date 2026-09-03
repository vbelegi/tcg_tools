"""Promotional actions API — CRUD, publishing, filters and regulation upload."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import StaffAuditLog

PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n%%EOF\n"
RAFFLE = "raffle_purchase_right"


def _payload(**overrides) -> dict:
    body = {
        "name": "Pré-venda Booster Box",
        "type": RAFFLE,
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=7)).isoformat(),
        "description": "Direito de compra do produto limitado.",
    }
    body.update(overrides)
    return body


def _create(client: TestClient, **overrides) -> dict:
    r = client.post("/api/v1/acoes", json=_payload(**overrides))
    assert r.status_code == 201, r.text
    return r.json()


def test_create_applies_agreed_defaults(api_client: TestClient):
    action = _create(api_client)

    assert action["published"] is False
    assert action["show_in_calendar"] is True
    assert action["max_participants"] is None
    assert action["regulation"] is None
    assert action["type_label"] == "Sorteio de Direito de Compra Físico"
    assert "presencial" in action["how_to_participate"]


def test_create_rejects_unknown_type_and_inverted_period(api_client: TestClient):
    bad_type = api_client.post("/api/v1/acoes", json=_payload(type="sorteio_online"))
    assert bad_type.status_code == 400

    inverted = api_client.post(
        "/api/v1/acoes",
        json=_payload(
            start_date=(date.today() + timedelta(days=5)).isoformat(),
            end_date=date.today().isoformat(),
        ),
    )
    assert inverted.status_code == 400


def test_draft_is_invisible_to_public(api_client: TestClient):
    draft = _create(api_client, name="Rascunho Interno")
    published = _create(api_client, name="Ação Publicada")
    assert api_client.post(f"/api/v1/acoes/{published['id']}/publish").status_code == 200

    staff_list = api_client.get("/api/v1/acoes").json()
    assert {a["id"] for a in staff_list} == {draft["id"], published["id"]}
    assert staff_list[0]["participant_count"] == 0

    api_client.post("/api/v1/auth/logout")

    public_list = api_client.get("/api/v1/acoes").json()
    assert {a["id"] for a in public_list} == {published["id"]}
    assert "participant_count" not in public_list[0]

    assert api_client.get(f"/api/v1/acoes/{draft['id']}").status_code == 404
    assert api_client.get(f"/api/v1/acoes/{published['id']}").status_code == 200


def test_search_filter_cannot_surface_a_draft(api_client: TestClient):
    draft = _create(api_client, name="Segredo Booster")
    api_client.post("/api/v1/auth/logout")

    found = api_client.get("/api/v1/acoes", params={"q": "Segredo"}).json()
    assert found == []
    assert api_client.get(f"/api/v1/acoes/{draft['id']}").status_code == 404


def test_search_and_active_filters(api_client: TestClient):
    ongoing = _create(api_client, name="Pré-venda Alpha")
    ended = _create(
        api_client,
        name="Pré-venda Beta",
        start_date=(date.today() - timedelta(days=10)).isoformat(),
        end_date=(date.today() - timedelta(days=2)).isoformat(),
    )

    by_name = api_client.get("/api/v1/acoes", params={"q": "alpha"}).json()
    assert [a["id"] for a in by_name] == [ongoing["id"]]

    only_active = api_client.get("/api/v1/acoes", params={"active": "true"}).json()
    assert [a["id"] for a in only_active] == [ongoing["id"]]

    everything = api_client.get("/api/v1/acoes").json()
    assert {a["id"] for a in everything} == {ongoing["id"], ended["id"]}


def test_type_cannot_change_after_creation(api_client: TestClient):
    action = _create(api_client)

    blocked = api_client.patch(
        f"/api/v1/acoes/{action['id']}", json={"type": "outro_tipo", "name": "Novo Nome"}
    )
    assert blocked.status_code == 400
    assert "tipo" in blocked.json()["detail"].lower()

    unchanged = api_client.get(f"/api/v1/acoes/{action['id']}").json()
    assert unchanged["name"] == action["name"]

    same_type = api_client.patch(
        f"/api/v1/acoes/{action['id']}", json={"type": RAFFLE, "name": "Nome Atualizado"}
    )
    assert same_type.status_code == 200
    assert same_type.json()["name"] == "Nome Atualizado"


def test_edit_records_a_diff_in_the_audit_log(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    new_end = (date.today() + timedelta(days=20)).isoformat()

    r = api_client.patch(
        f"/api/v1/acoes/{action['id']}",
        json={"end_date": new_end, "show_in_calendar": False},
    )
    assert r.status_code == 200
    assert r.json()["show_in_calendar"] is False

    entry = (
        db_session.query(StaffAuditLog)
        .filter(StaffAuditLog.action == "promo.edit")
        .order_by(StaffAuditLog.id.desc())
        .first()
    )
    assert entry is not None
    changes = entry.meta["changes"]
    assert changes["end_date"]["to"] == new_end
    assert changes["show_in_calendar"] == {"from": True, "to": False}
    assert "name" not in changes


def test_edit_without_real_change_does_not_audit(api_client: TestClient, db_session: Session):
    action = _create(api_client)
    before = db_session.query(StaffAuditLog).filter(StaffAuditLog.action == "promo.edit").count()

    r = api_client.patch(f"/api/v1/acoes/{action['id']}", json={"name": action["name"]})
    assert r.status_code == 200

    after = db_session.query(StaffAuditLog).filter(StaffAuditLog.action == "promo.edit").count()
    assert after == before


def test_publish_is_idempotent(api_client: TestClient, db_session: Session):
    action = _create(api_client)

    first = api_client.post(f"/api/v1/acoes/{action['id']}/publish")
    second = api_client.post(f"/api/v1/acoes/{action['id']}/publish")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["published"] is True

    audits = (
        db_session.query(StaffAuditLog).filter(StaffAuditLog.action == "promo.publish").count()
    )
    assert audits == 1


def test_regulation_upload_versions_and_keeps_previous(api_client: TestClient):
    action = _create(api_client)
    action_id = action["id"]

    first = api_client.post(
        f"/api/v1/acoes/{action_id}/regulamento",
        files={"file": ("qualquer-nome-do-staff.pdf", PDF, "application/pdf")},
    )
    assert first.status_code == 200, first.text
    assert first.json()["regulation"] == {
        "version": 1,
        "display_name": "Pré-venda Booster Box v1",
        "url": f"/api/v1/media/acoes/{action_id}/regulamento",
    }

    second = api_client.post(
        f"/api/v1/acoes/{action_id}/regulamento",
        files={"file": ("outro.pdf", PDF + b"v2", "application/pdf")},
    )
    assert second.status_code == 200
    body = second.json()
    assert body["regulation"]["version"] == 2
    assert [v["version"] for v in body["regulation_versions"]] == [2, 1]

    folder = get_settings().resolved_promo_regulations_dir / str(action_id)
    assert (folder / "v1.pdf").is_file()
    assert (folder / "v2.pdf").is_file()


def test_regulation_label_follows_current_action_name(api_client: TestClient):
    action = _create(api_client)
    api_client.post(
        f"/api/v1/acoes/{action['id']}/regulamento",
        files={"file": ("x.pdf", PDF, "application/pdf")},
    )

    renamed = api_client.patch(
        f"/api/v1/acoes/{action['id']}", json={"name": "Pré-venda Renomeada"}
    )
    assert renamed.json()["regulation"]["display_name"] == "Pré-venda Renomeada v1"


def test_regulation_rejects_non_pdf(api_client: TestClient):
    action = _create(api_client)

    wrong_type = api_client.post(
        f"/api/v1/acoes/{action['id']}/regulamento",
        files={"file": ("regulamento.png", b"\x89PNG\r\n", "image/png")},
    )
    assert wrong_type.status_code == 400

    lying_content_type = api_client.post(
        f"/api/v1/acoes/{action['id']}/regulamento",
        files={"file": ("regulamento.pdf", b"not a pdf at all", "application/pdf")},
    )
    assert lying_content_type.status_code == 400

    assert api_client.get(f"/api/v1/acoes/{action['id']}").json()["regulation"] is None


def test_regulation_download_respects_publication(api_client: TestClient):
    action = _create(api_client)
    action_id = action["id"]
    api_client.post(
        f"/api/v1/acoes/{action_id}/regulamento",
        files={"file": ("x.pdf", PDF, "application/pdf")},
    )

    as_staff = api_client.get(f"/api/v1/media/acoes/{action_id}/regulamento")
    assert as_staff.status_code == 200
    assert as_staff.headers["content-type"] == "application/pdf"
    assert "pre-venda-booster-box-v1.pdf" in as_staff.headers["content-disposition"]

    api_client.post("/api/v1/auth/logout")
    assert api_client.get(f"/api/v1/media/acoes/{action_id}/regulamento").status_code == 404
    assert (
        api_client.get(f"/api/v1/media/acoes/{action_id}/regulamento/1").status_code == 401
    )

    api_client.post("/api/v1/auth/login", json={"email": "admin@local", "password": "testpass12"})
    api_client.post(f"/api/v1/acoes/{action_id}/publish")
    api_client.post("/api/v1/auth/logout")

    assert api_client.get(f"/api/v1/media/acoes/{action_id}/regulamento").status_code == 200


def test_types_endpoint_is_staff_only(api_client: TestClient):
    listed = api_client.get("/api/v1/acoes/tipos")
    assert listed.status_code == 200
    assert listed.json() == [
        {"key": RAFFLE, "label": "Sorteio de Direito de Compra Físico"}
    ]

    api_client.post("/api/v1/auth/logout")
    assert api_client.get("/api/v1/acoes/tipos").status_code == 401
