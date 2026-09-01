"""Invite provisioning with optional email delivery."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session as DbSession

from app.core.auth.service import create_invite
from app.core.email.outbound import send_invite_email
from app.models import InviteToken, User

logger = logging.getLogger(__name__)


def provision_invite_and_email(db: DbSession, user: User) -> InviteToken:
    """Create invite token and send email."""
    invite = create_invite(db, user)
    try:
        send_invite_email(user, invite.token)
    except Exception:
        logger.exception("Failed to send invite email to user_id=%s", user.id)
    return invite
