"""Avatar processing unit tests."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.core.auth.avatars import (
    MAX_UPLOAD_BYTES,
    AvatarError,
    encode_user_avatar,
    user_avatar_url,
)


def _png_bytes(size: int = 40) -> bytes:
    img = Image.new("RGB", (size, size), color=(200, 80, 40))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_encode_user_avatar_returns_webp_bytes():
    data = _png_bytes(120)
    blob = encode_user_avatar(data, "image/png")
    assert isinstance(blob, bytes)
    assert len(blob) < MAX_UPLOAD_BYTES
    out = Image.open(io.BytesIO(blob))
    assert out.size == (256, 256)
    assert out.format == "WEBP"


def test_encode_user_avatar_rejects_large_file():
    with pytest.raises(AvatarError, match="grande"):
        encode_user_avatar(b"x" * (MAX_UPLOAD_BYTES + 1), "image/png")


def test_encode_user_avatar_rejects_bad_type():
    with pytest.raises(AvatarError, match="Formato"):
        encode_user_avatar(_png_bytes(), "image/gif")


def test_user_avatar_url():
    assert user_avatar_url(1, None) is None
    assert user_avatar_url(1, b"webp") == "/api/v1/media/avatars/1"
