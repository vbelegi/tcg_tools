"""High-level send helpers for auth flows."""

from __future__ import annotations

import logging

from app.core.auth.invites import (
    email_verify_url,
    invite_claim_url,
    password_reset_url,
    promo_action_url,
)
from app.core.auth.service import EMAIL_VERIFY_HOURS, INVITE_DAYS, PASSWORD_RESET_DAYS
from app.core.email.service import get_email_service
from app.core.email.templates import (
    invite_email,
    password_reset_email,
    promo_update_email,
    verification_email,
)
from app.models import User

logger = logging.getLogger(__name__)

_GENERIC_FORGOT_MSG = "Se existir uma conta com esse e-mail, você receberá um link em breve."


def send_verification_email(user: User, raw_token: str) -> None:
    url = email_verify_url(raw_token)
    if not url:
        logger.warning("TCGTOOLS_PUBLIC_BASE_URL unset; cannot send verification email to %s", user.email)
        return
    subject, text, html = verification_email(verify_url=url, hours=EMAIL_VERIFY_HOURS)
    get_email_service().send(to=user.email, subject=subject, text_body=text, html_body=html)


def send_invite_email(user: User, invite_token: str) -> None:
    url = invite_claim_url(invite_token)
    if not url:
        logger.warning("TCGTOOLS_PUBLIC_BASE_URL unset; cannot send invite email to %s", user.email)
        return
    subject, text, html = invite_email(claim_url=url, display_name=user.display_name, days=INVITE_DAYS)
    get_email_service().send(to=user.email, subject=subject, text_body=text, html_body=html)


def send_password_reset_email(user: User, raw_token: str) -> None:
    url = password_reset_url(raw_token)
    if not url:
        logger.warning("TCGTOOLS_PUBLIC_BASE_URL unset; cannot send password reset email to %s", user.email)
        return
    subject, text, html = password_reset_email(reset_url=url, days=PASSWORD_RESET_DAYS)
    get_email_service().send(to=user.email, subject=subject, text_body=text, html_body=html)


def send_promo_update_email(
    user: User,
    *,
    action_name: str,
    action_id: int,
    change_lines: list[str],
) -> None:
    url = promo_action_url(action_id) or f"/acoes/{action_id}"
    subject, text, html = promo_update_email(
        display_name=user.display_name,
        action_name=action_name,
        action_url=url,
        change_lines=change_lines,
    )
    get_email_service().send(to=user.email, subject=subject, text_body=text, html_body=html)


def forgot_password_generic_message() -> str:
    return _GENERIC_FORGOT_MSG
