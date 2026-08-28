"""Session cookie helpers (Secure flag when serving over HTTPS)."""

from __future__ import annotations

from fastapi import Response

from app.config import get_settings
from app.core.auth.service import SESSION_COOKIE, SESSION_DAYS


def _cookie_kwargs() -> dict:
    return {
        "httponly": True,
        "samesite": "lax",
        "max_age": SESSION_DAYS * 24 * 3600,
        "path": "/",
        "secure": get_settings().resolved_cookie_secure,
    }


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(key=SESSION_COOKIE, value=token, **_cookie_kwargs())


def clear_session_cookie(response: Response) -> None:
    kwargs = _cookie_kwargs()
    response.delete_cookie(
        key=SESSION_COOKIE,
        path=kwargs["path"],
        secure=kwargs["secure"],
        httponly=kwargs["httponly"],
        samesite=kwargs["samesite"],
    )
