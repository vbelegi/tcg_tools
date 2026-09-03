"""Privacy / LGPD constants and marketing contact gate."""

from __future__ import annotations

from datetime import date

from app.models import User, UserStatus

PRIVACY_POLICY_VERSION = "1.0"
TERMS_VERSION = "1.0"
INCOMPLETE_PURGE_DAYS = 180
ANONYMOUS_DISPLAY_NAME = "Anônimo"
MIN_MARKETING_AGE = 18


def age_years(birth_date: date | None, *, today: date | None = None) -> int | None:
    if birth_date is None:
        return None
    ref = today or date.today()
    years = ref.year - birth_date.year
    if (ref.month, ref.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def can_contact_for_marketing(user: User, *, today: date | None = None) -> bool:
    """WhatsApp/email commercial contact eligibility (opt-out model)."""
    if user.status != UserStatus.active.value:
        return False
    if bool(getattr(user, "marketing_opt_out", False)):
        return False
    phone = (user.phone or "").strip()
    if not phone:
        return False
    age = age_years(user.birth_date, today=today)
    if age is not None and age < MIN_MARKETING_AGE:
        return False
    return True
