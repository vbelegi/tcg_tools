"""Avatar upload processing (square resize + WebP bytes in DB)."""

from __future__ import annotations

import io

from PIL import Image

MAX_UPLOAD_BYTES = 512 * 1024
AVATAR_PX = 256
ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})


class AvatarError(Exception):
    pass


def encode_user_avatar(data: bytes, content_type: str | None) -> bytes:
    """Validate, crop/resize to square WebP; return bytes for users.avatar_blob."""
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

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=82, method=4)
    return buf.getvalue()


def user_avatar_url(user_id: int, avatar_blob: bytes | None) -> str | None:
    if not avatar_blob:
        return None
    return f"/api/v1/media/avatars/{user_id}"
