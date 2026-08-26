"""Avatar upload processing (square resize + WebP)."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from app.config import get_settings

MAX_UPLOAD_BYTES = 512 * 1024
AVATAR_PX = 256
ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})


class AvatarError(Exception):
    pass


def save_user_avatar(user_id: int, data: bytes, content_type: str | None) -> str:
    """Validate, crop/resize to square WebP, write under data/media/avatars.

    Returns relative path suitable for StaticFiles mount (e.g. ``avatars/user_1.webp``).
    """
    if content_type and content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise AvatarError("Formato inválido. Use JPEG, PNG ou WebP.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise AvatarError(f"Arquivo muito grande (máx. {MAX_UPLOAD_BYTES // 1024} KB).")
    if not data:
        raise AvatarError("Arquivo vazio.")

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:
        raise AvatarError("Não foi possível ler a imagem.") from exc

    img = img.convert("RGBA") if img.mode in ("P", "RGBA", "LA") else img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((AVATAR_PX, AVATAR_PX), Image.Resampling.LANCZOS)
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (18, 8, 26))
        background.paste(img, mask=img.split()[3])
        img = background
    else:
        img = img.convert("RGB")

    settings = get_settings()
    settings.resolved_avatars_dir.mkdir(parents=True, exist_ok=True)
    rel = f"avatars/user_{user_id}.webp"
    dest = settings.resolved_media_dir / rel
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=82, method=4)
    dest.write_bytes(buf.getvalue())
    return rel.replace("\\", "/")


def delete_user_avatar_file(avatar_path: str | None) -> None:
    if not avatar_path:
        return
    path = get_settings().resolved_media_dir / avatar_path
    if path.is_file():
        path.unlink(missing_ok=True)


def media_url(avatar_path: str | None) -> str | None:
    if not avatar_path:
        return None
    return f"/media/{avatar_path.lstrip('/')}"
