"""Transactional email (SMTP in production, console log in development)."""

from app.core.email.outbound import (
    send_invite_email,
    send_password_reset_email,
    send_promo_update_email,
    send_verification_email,
)
from app.core.email.service import get_email_service

__all__ = [
    "get_email_service",
    "send_invite_email",
    "send_password_reset_email",
    "send_promo_update_email",
    "send_verification_email",
]
