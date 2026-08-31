"""Unit tests for session token hashing and search escaping."""

from __future__ import annotations

from app.core.auth.session_tokens import generate_session_token, hash_session_token, verify_session_token
from app.core.search import escape_like, ilike_contains


def test_session_token_hash_roundtrip():
    token = generate_session_token()
    hashed = hash_session_token(token)
    assert hashed != token
    assert len(hashed) == 64
    assert verify_session_token(token, hashed)
    assert not verify_session_token("other", hashed)


def test_escape_like_wildcards():
    assert escape_like("100%") == "100\\%"
    assert escape_like("a_b") == "a\\_b"
    assert ilike_contains("x%y") == "%x\\%y%"
