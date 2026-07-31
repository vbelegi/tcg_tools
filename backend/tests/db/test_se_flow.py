"""Single elimination flow tests."""

from __future__ import annotations

from datetime import date

import pytest

from app.services.torneio_service import TorneioService
from tests.conftest import score_all_matches


@pytest.fixture
def se_event(torneio_service: TorneioService):
    event = torneio_service.create_event(
        name="SE Test",
        event_date=date.today(),
        format="single_elimination",
        max_rounds=None,
        entry_fee=10.0,
        best_of=1,
        premiacao_preset_id="standard",
    )
    for name in ("A", "B", "C", "D"):
        torneio_service.add_player(event.id, name)
    return event


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
