"""Password hashing and validation."""

from __future__ import annotations

import bcrypt

ADMIN_USERNAME = "admin"
MIN_PASSWORD_LEN = 6


class AuthError(ValueError):
    pass


def validate_password_plain(password: str) -> str:
    if not isinstance(password, str) or password == "":
        raise AuthError("Senha é obrigatória.")
    if len(password) < MIN_PASSWORD_LEN:
        raise AuthError(f"Senha deve ter pelo menos {MIN_PASSWORD_LEN} caracteres.")
    return password


def hash_password(password: str) -> str:
    validate_password_plain(password)
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False
