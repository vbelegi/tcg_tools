"""Avatar processing unit tests."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.core.auth.avatars import (
    MAX_UPLOAD_BYTES,
    AvatarError,
    media_url,
    save_user_avatar,
)


def _png_bytes(size: int = 40) -> bytes:
    img = Image.new("RGB", (size, size), color=(200, 80, 40))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_save_user_avatar_writes_webp(alembic_db_url: str, tmp_path, monkeypatch):
    # alembic_db_url fixture already sets TCGTOOLS_DATA_DIR via monkeypatch
    data = _png_bytes(120)
    rel = save_user_avatar(42, data, "image/png")
    assert rel == "avatars/user_42.webp"
    from app.config import get_settings

    path = get_settings().resolved_media_dir / rel
    assert path.is_file()
    assert path.stat().st_size < MAX_UPLOAD_BYTES
    out = Image.open(path)
    assert out.size == (256, 256)


def test_save_user_avatar_rejects_large_file():
    with pytest.raises(AvatarError, match="grande"):
        save_user_avatar(1, b"x" * (MAX_UPLOAD_BYTES + 1), "image/png")


def test_save_user_avatar_rejects_bad_type():
    with pytest.raises(AvatarError, match="Formato"):
        save_user_avatar(1, _png_bytes(), "image/gif")


def test_media_url():
    assert media_url(None) is None
    assert media_url("avatars/user_1.webp") == "/media/avatars/user_1.webp"
