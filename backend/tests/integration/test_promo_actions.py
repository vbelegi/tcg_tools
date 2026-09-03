"""Promotional actions — schema and visibility rules."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.promo_visibility import (
    PROMO_PUBLIC_WINDOW_DAYS,
    can_view_promo,
    visible_promo_query,
)
from app.models import (
    PromoAction,
    PromoActionType,
    PromoParticipant,
    PromoParticipantStatus,
    User,
    UserRole,
    UserStatus,
)

PROMO_TABLES = (
    "promo_actions",
    "promo_regulation_versions",
    "promo_enrollment_tokens",
    "promo_participants",
    "promo_draw_results",
)


def _alembic_cfg(db_url: str) -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _user(
    db: Session,
    *,
    email: str,
    role: str = UserRole.player.value,
    name: str = "Usuário",
) -> User:
    user = User(email=email, display_name=name, role=role, status=UserStatus.active.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _action(
    db: Session,
    *,
    name: str = "Pré-venda",
    published: bool = True,
    ends_in_days: int = 3,
) -> PromoAction:
    end = date.today() + timedelta(days=ends_in_days)
    action = PromoAction(
        name=name,
        type=PromoActionType.raffle_purchase_right.value,
        start_date=end - timedelta(days=5),
        end_date=end,
        published=published,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def test_action_defaults(db_session: Session) -> None:
    action = _action(db_session, published=False)

    assert action.published is False
    assert action.show_in_calendar is True
    assert action.max_participants is None
    assert action.regulation_version is None


def test_staff_sees_drafts_and_public_does_not(db_session: Session) -> None:
    draft = _action(db_session, name="Rascunho", published=False)
    live = _action(db_session, name="Publicada", published=True)
    admin = _user(db_session, email="admin.promo@test.local", role=UserRole.admin.value)
    staff = _user(db_session, email="staff.promo@test.local", role=UserRole.staff.value)
    player = _user(db_session, email="player.promo@test.local")

    assert {a.id for a in visible_promo_query(db_session, admin)} == {draft.id, live.id}
    assert {a.id for a in visible_promo_query(db_session, staff)} == {draft.id, live.id}
    assert {a.id for a in visible_promo_query(db_session, player)} == {live.id}
    assert {a.id for a in visible_promo_query(db_session, None)} == {live.id}


def test_public_listing_drops_action_after_window(db_session: Session) -> None:
    recent = _action(db_session, name="Recente", ends_in_days=-(PROMO_PUBLIC_WINDOW_DAYS - 1))
    old = _action(db_session, name="Antiga", ends_in_days=-(PROMO_PUBLIC_WINDOW_DAYS + 1))
    staff = _user(db_session, email="staff.window@test.local", role=UserRole.staff.value)
    player = _user(db_session, email="player.window@test.local")

    assert {a.id for a in visible_promo_query(db_session, player)} == {recent.id}
    assert {a.id for a in visible_promo_query(db_session, staff)} == {recent.id, old.id}

    assert can_view_promo(old, staff) is True
    assert can_view_promo(old, player) is False
    assert can_view_promo(old, None) is False
    assert can_view_promo(recent, player) is True


def test_user_may_join_several_actions_but_only_once_each(db_session: Session) -> None:
    first = _action(db_session, name="Ação 1")
    second = _action(db_session, name="Ação 2")
    user = _user(db_session, email="multi.promo@test.local")

    for action in (first, second):
        db_session.add(
            PromoParticipant(
                promo_id=action.id,
                user_id=user.id,
                status=PromoParticipantStatus.confirmed.value,
            )
        )
    db_session.commit()

    db_session.add(
        PromoParticipant(
            promo_id=first.id,
            user_id=user.id,
            status=PromoParticipantStatus.confirmed.value,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_migration_015_round_trip(alembic_db_url: str) -> None:
    cfg = _alembic_cfg(alembic_db_url)
    engine = create_engine(alembic_db_url)
    try:
        assert set(PROMO_TABLES) <= set(inspect(engine).get_table_names())

        command.downgrade(cfg, "014")
        after_downgrade = set(inspect(engine).get_table_names())
        assert not (set(PROMO_TABLES) & after_downgrade)
        assert "staff_audit_logs" in after_downgrade

        command.upgrade(cfg, "head")
        assert set(PROMO_TABLES) <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
