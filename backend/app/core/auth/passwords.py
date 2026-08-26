"""Password hashing and validation."""

from __future__ import annotations

import bcrypt

ADMIN_EMAIL = "admin@local"
MIN_PASSWORD_LEN = 6


class AuthError(ValueError):
    pass


def validate_password_plain(password: str) -> str:
    if not isinstance(password, str) or password == "":
        raise AuthError("Senha é obrigatória.")
    if len(password) < MIN_PASSWORD_LEN:
        raise AuthError(f"Senha deve ter pelo menos {MIN_PASSWORD_LEN} caracteres.")
    return password


def normalize_email(email: str) -> str:
    value = (email or "").strip().lower()
    if not value or "@" not in value:
        raise AuthError("E-mail inválido.")
    return value


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if len(digits) < 10 or len(digits) > 13:
        raise AuthError("Celular inválido. Use DDD + número (10 a 13 dígitos).")
    return digits


def hash_password(password: str) -> str:
    validate_password_plain(password)
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("ascii")


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False
