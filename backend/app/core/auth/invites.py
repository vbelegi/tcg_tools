"""Invite / password-reset link helpers (absolute URL from public_base_url)."""

from __future__ import annotations

from app.config import get_settings


def invite_claim_path(token: str) -> str:
    return f"/convite/{token}"


def invite_claim_url(token: str) -> str | None:
    base = (get_settings().public_base_url or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}{invite_claim_path(token)}"


def password_reset_path(token: str) -> str:
    return f"/redefinir-senha/{token}"


def password_reset_url(token: str) -> str | None:
    base = (get_settings().public_base_url or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}{password_reset_path(token)}"


def email_verify_path(token: str) -> str:
    return f"/verificar-email/{token}"


def email_verify_url(token: str) -> str | None:
    base = (get_settings().public_base_url or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}{email_verify_path(token)}"


def promo_enroll_path(token: str) -> str:
    return f"/acoes/participar/{token}"


def promo_enroll_url(token: str) -> str | None:
    base = (get_settings().public_base_url or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}{promo_enroll_path(token)}"
