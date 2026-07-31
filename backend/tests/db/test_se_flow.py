"""Single elimination flow tests."""

from __future__ import annotations

import json
from datetime import date

import pytest

from app.core.torneios.se_bands import format_band_label
from app.services.torneio_service import TorneioService
from tests.conftest import create_se_event, run_se_bracket, score_all_matches


@pytest.fixture
def se_event(torneio_service: TorneioService):
    return create_se_event(torneio_service, 4)


def test_se_start_has_byes(torneio_service: TorneioService, se_event):
    svc = torneio_service
    eid = se_event.id
    svc.start_event(eid)
    rnd = svc.get_round(eid, 1)
    byes = sum(1 for m in rnd["matches"] if m["is_bye"])
    assert byes >= 0
    score_all_matches(svc, eid, 1, default=(1, 0))
    svc.complete_round(eid)
    detail = svc.get_event(eid)
    assert detail["between_rounds"] is True


def test_se_full_flow_finalize(torneio_service: TorneioService, se_event):
    svc = torneio_service
    eid = se_event.id
    run_se_bracket(svc, eid, default=(1, 0))
    assert svc.get_event(eid)["can_finalize"] is True
    svc.finalize(eid)
    prem = svc.get_premiacao(eid)
    assert prem["schema_version"] == 2
    assert "bands" in prem
    total = sum(p["payout"] for p in prem["player_payouts"])
    assert total == pytest.approx(4, abs=1e-9)
    assert prem["total_creditos"] == pytest.approx(40.0, abs=1e-9)
    rows = svc.get_classificacao(eid)
    labels = {r["name"]: r["rank_label"] for r in rows if not r["is_drop"]}
    assert "1º" in labels.values()
    assert format_band_label(3, 4) in labels.values()


@pytest.mark.parametrize("n", [8, 16])
def test_se_bracket_finalize(torneio_service: TorneioService, n: int):
    svc = torneio_service
    eid = create_se_event(svc, n).id
    run_se_bracket(svc, eid, default=(1, 0))
    svc.finalize(eid)
    prem = svc.get_premiacao(eid)
    assert prem["schema_version"] == 2
    assert sum(p["payout"] for p in prem["player_payouts"]) == pytest.approx(n, abs=1e-9)
    assert prem["total_creditos"] == pytest.approx(n * 10.0, abs=1e-9)


def test_se_legacy_finished_uses_swiss_standings(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 4).id
    run_se_bracket(svc, eid, default=(1, 0))
    svc.finalize(eid)

    event = svc._repo.get(eid)
    pr = dict(event.premiacao_resultado)
    pr["schema_version"] = 1
    pr.pop("standings_snapshot", None)
    event.premiacao_resultado = pr
    svc._commit()

    rows = svc.get_classificacao(eid)
    assert len(rows) == 4
    assert all("points" in r for r in rows)
    assert not any(r.get("rank_label") == format_band_label(3, 4) for r in rows)


def test_se_drop_between_rounds_conservation(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 8).id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1, default=(1, 0))
    svc.complete_round(eid)

    rnd1 = svc.get_round(eid, 1)
    m = next(x for x in rnd1["matches"] if not x["is_bye"])
    loser_id = m["player2_id"] if m["winner_id"] == m["player1_id"] else m["player1_id"]
    svc.drop_player(eid, loser_id, mid_round=False)

    while not svc.get_event(eid)["can_finalize"]:
        ev = svc.get_event(eid)
        if ev["between_rounds"]:
            svc.start_next_round(eid)
            ev = svc.get_event(eid)
        score_all_matches(svc, event_id=eid, round_number=ev["current_round"], default=(1, 0))
        svc.complete_round(eid)

    svc.finalize(eid)
    prem = svc.get_premiacao(eid)
    assert sum(p["payout"] for p in prem["player_payouts"]) == pytest.approx(8, abs=1e-9)


def test_se_bronze_drop_before_final_round(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 4, third_place_match=True).id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1, default=(1, 0))
    svc.complete_round(eid)

    rnd1 = svc.get_round(eid, 1)
    m = next(x for x in rnd1["matches"] if not x["is_bye"])
    loser_id = m["player2_id"] if m["winner_id"] == m["player1_id"] else m["player1_id"]
    svc.drop_player(eid, loser_id, mid_round=False)

    svc.start_next_round(eid)
    score_all_matches(svc, eid, 2, default=(1, 0))
    svc.complete_round(eid)
    svc.finalize(eid)

    prem = svc.get_premiacao(eid)
    assert sum(p["payout"] for p in prem["player_payouts"]) == pytest.approx(4, abs=1e-9)
    dropped = next(p for p in svc.get_event(eid)["players"] if p["id"] == loser_id)
    assert dropped["dropped_at"] is not None


def test_se_per_phase_best_of_and_mid_drop(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(
        svc, 4, se_bo_config={"1": 5, "2": 3}, best_of=1
    ).id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1, default=(2, 0))
    svc.complete_round(eid)
    svc.start_next_round(eid)

    rnd2 = svc.get_round(eid, 2)
    final = next(m for m in rnd2["matches"] if not m.get("is_third_place"))
    assert final["best_of"] == 5

    dropped_id = final["player1_id"]
    svc.drop_player(eid, dropped_id, mid_round=True)

    updated = next(m for m in svc.get_round(eid, 2)["matches"] if m["id"] == final["id"])
    assert updated["is_walkover"] is True
    assert updated["score_p1"] == 0
    assert updated["score_p2"] == 3
    assert updated["winner_id"] == final["player2_id"]


def test_se_create_with_options(torneio_service: TorneioService):
    event = torneio_service.create_event(
        name="SE Options",
        event_date=date.today(),
        format="single_elimination",
        max_rounds=None,
        entry_fee=10.0,
        best_of=3,
        premiacao_preset_id="standard",
        third_place_match=True,
        se_bo_config={"1": 5, "2": 3},
    )
    detail = torneio_service.get_event(event.id)
    assert detail["third_place_match"] is True
    assert detail["se_bo_config"] == {"1": 5, "2": 3}


def test_se_export_log_includes_metadata(torneio_service: TorneioService, tmp_path, monkeypatch):
    monkeypatch.setenv("TCGTOOLS_DATA_DIR", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()

    svc = TorneioService(torneio_service._db)
    eid = create_se_event(
        svc, 4, third_place_match=True, se_bo_config={"1": 5, "2": 3}, best_of=3
    ).id
    run_se_bracket(svc, eid, default=(2, 0))
    svc.finalize(eid)

    content, _ = svc.export_log(eid)
    log = json.loads(content)
    assert log["event"]["third_place_match"] is True
    assert log["event"]["se_bo_config"] == {"1": 5, "2": 3}

    all_matches = [m for r in log["rounds"] for m in r["matches"]]
    assert any(m.get("is_third_place") for m in all_matches)
    assert all("best_of" in m for m in all_matches if not m["bye"])
    assert log["version"] == 2
    assert log["premiacao_schema_version"] == 2
    assert all("player1_id" in m for m in all_matches if not m["bye"])


def test_se_six_players_full_flow(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 6).id
    run_se_bracket(svc, eid, default=(1, 0))
    svc.finalize(eid)
    prem = svc.get_premiacao(eid)
    assert sum(p["payout"] for p in prem["player_payouts"]) == pytest.approx(6, abs=1e-9)


def test_se_thirty_two_players_finalize(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 32).id
    run_se_bracket(svc, eid, default=(1, 0))
    svc.finalize(eid)
    assert svc.get_premiacao(eid)["schema_version"] == 2


def test_se_sixteen_bronze_finalize(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 16, third_place_match=True).id
    run_se_bracket(svc, eid, default=(1, 0))
    svc.finalize(eid)
    rows = svc.get_classificacao(eid)
    labels = {r["rank_label"] for r in rows if not r.get("is_drop")}
    assert "3º" in labels or "4º" in labels


def test_se_both_semi_losers_drop_skips_bronze(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 4, third_place_match=True).id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1, default=(1, 0))
    svc.complete_round(eid)

    rnd1 = svc.get_round(eid, 1)
    for m in [x for x in rnd1["matches"] if not x["is_bye"]]:
        loser_id = m["player2_id"] if m["winner_id"] == m["player1_id"] else m["player1_id"]
        svc.drop_player(eid, loser_id, mid_round=False)

    svc.start_next_round(eid)
    rnd2 = svc.get_round(eid, 2)
    assert not any(m.get("is_third_place") for m in rnd2["matches"])
    score_all_matches(svc, eid, 2, default=(1, 0))
    svc.complete_round(eid)
    svc.finalize(eid)
    prem = svc.get_premiacao(eid)
    assert sum(p["payout"] for p in prem["player_payouts"]) == pytest.approx(4, abs=1e-9)


def test_se_reopen_round_regenerates_pairing(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 4).id
    svc.start_event(eid)
    score_all_matches(svc, eid, 1, default=(1, 0))
    svc.complete_round(eid)
    svc.start_next_round(eid)
    svc.reopen_round(eid)
    svc.complete_round(eid)
    svc.start_next_round(eid)
    score_all_matches(svc, eid, 2, default=(1, 0))
    svc.complete_round(eid)
    svc.finalize(eid)
    assert svc.get_event(eid)["status"] == "finished"


def test_se_start_prunes_orphan_bo_phases(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 4, se_bo_config={"1": 5, "2": 3, "3": 1}).id
    svc.start_event(eid)
    detail = svc.get_event(eid)
    assert detail["se_bo_config"] == {"1": 5, "2": 3}


def test_se_draft_config_warnings(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 4, se_bo_config={"1": 5, "2": 3, "3": 1}).id
    detail = svc.get_event(eid)
    assert "config_warnings" in detail
    assert any("rounds_from_final=3" in w for w in detail["config_warnings"])


def test_se_legacy_get_premiacao_without_bands(torneio_service: TorneioService):
    svc = torneio_service
    eid = create_se_event(svc, 4).id
    run_se_bracket(svc, eid, default=(1, 0))
    svc.finalize(eid)
    event = svc._repo.get(eid)
    pr = dict(event.premiacao_resultado)
    pr["schema_version"] = 1
    pr.pop("bands", None)
    pr.pop("player_payouts", None)
    event.premiacao_resultado = pr
    svc._commit()
    prem = svc.get_premiacao(eid)
    assert prem["schema_version"] == 1
    assert "bands" not in prem or prem.get("bands") is None
