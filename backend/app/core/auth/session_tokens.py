"""Session cookie token hashing (store hash only in DB)."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_session_token(token: str, token_hash: str) -> bool:
    if not token or not token_hash:
        return False
    expected = hash_session_token(token)
    return hmac.compare_digest(expected, token_hash)
