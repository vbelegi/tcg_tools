"""Whether a user may occupy a promotional-action slot as confirmed."""

from __future__ import annotations

from app.core.auth.service import is_email_verified
from app.models import User, UserStatus


def is_account_contactable(user: User) -> bool:
    """Active account with verified contact. Today that means e-mail; phone later."""
    status = user.status.value if hasattr(user.status, "value") else str(user.status)
    if status != UserStatus.active.value:
        return False
    return is_email_verified(user)
