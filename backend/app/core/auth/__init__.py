"""Auth package exports."""

from app.core.auth.passwords import ADMIN_EMAIL, AuthError, MIN_PASSWORD_LEN, hash_password, verify_password
from app.core.auth.service import (
    INVITE_DAYS,
    SESSION_COOKIE,
    SESSION_DAYS,
    authenticate,
    change_password,
    claim_invite,
    create_incomplete_user,
    create_invite,
    create_session,
    get_admin,
    get_user_by_email,
    get_user_for_token,
    private_user_dict,
    public_user_dict,
    register_player,
    revoke_session,
    upsert_admin_password,
)

# Back-compat alias used by older scripts/docs
ADMIN_USERNAME = "admin"

__all__ = [
    "ADMIN_EMAIL",
    "ADMIN_USERNAME",
    "AuthError",
    "INVITE_DAYS",
    "MIN_PASSWORD_LEN",
    "SESSION_COOKIE",
    "SESSION_DAYS",
    "authenticate",
    "change_password",
    "claim_invite",
    "create_incomplete_user",
    "create_invite",
    "create_session",
    "get_admin",
    "get_user_by_email",
    "get_user_for_token",
    "hash_password",
    "private_user_dict",
    "public_user_dict",
    "register_player",
    "revoke_session",
    "upsert_admin_password",
    "verify_password",
]
