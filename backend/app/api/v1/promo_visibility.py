"""Shared visibility rules for promotional actions.

Actions are never deleted; they simply drop off the public listing once they have
been over for PROMO_PUBLIC_WINDOW_DAYS. Staff and admin always see everything.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Query, Session

from app.api.v1.event_visibility import is_staff_user
from app.models import PromoAction, User

PROMO_PUBLIC_WINDOW_DAYS = 30


def promo_public_cutoff(today: date | None = None) -> date:
    return (today or date.today()) - timedelta(days=PROMO_PUBLIC_WINDOW_DAYS)


def visible_promo_query(db: Session, viewer: User | None) -> Query[PromoAction]:
    """Base query honouring who may see which actions.

    Search and status filters must be applied on top of this, never before it,
    so that a query string can never surface an unpublished action.
    """
    query = db.query(PromoAction)
    if is_staff_user(viewer):
        return query
    return query.filter(
        PromoAction.published.is_(True),
        PromoAction.end_date >= promo_public_cutoff(),
    )


def can_view_promo(action: PromoAction, viewer: User | None) -> bool:
    if is_staff_user(viewer):
        return True
    return bool(action.published) and action.end_date >= promo_public_cutoff()
