"""Regulation PDFs: versioned on disk, never stored under the uploaded filename.

Every upload creates a new version and the previous files are kept for audit.
What the user sees is always derived — "{nome da ação} v{N}" — so renaming an
action relabels the document without touching the version, which belongs to the
file rather than to the title.
"""

from __future__ import annotations

import unicodedata
from datetime import datetime
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PromoAction, PromoRegulationVersion, User

MAX_REGULATION_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = frozenset({"application/pdf"})


class RegulationError(ValueError):
    pass


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    out: list[str] = []
    prev_dash = False
    for ch in ascii_only:
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-") or "regulamento"


def action_dir(promo_id: int) -> Path:
    return get_settings().resolved_promo_regulations_dir / str(promo_id)


def regulation_path(promo_id: int, stored_name: str) -> Path:
    return action_dir(promo_id) / stored_name


def display_name(action: PromoAction, version: int) -> str:
    """Label shown in the UI. Follows the current action name, keeps the version."""
    return f"{action.name} v{version}"


def download_filename(action: PromoAction, version: int) -> str:
    """ASCII-safe name for Content-Disposition; never the uploaded filename."""
    return f"{_slugify(action.name)}-v{version}.pdf"


def validate_pdf(data: bytes, content_type: str | None) -> None:
    if content_type:
        base = content_type.split(";")[0].strip().lower()
        if base not in ALLOWED_CONTENT_TYPES:
            raise RegulationError("Formato inválido. Envie um arquivo PDF.")
    if not data:
        raise RegulationError("Arquivo vazio.")
    if len(data) > MAX_REGULATION_BYTES:
        raise RegulationError(
            f"Arquivo muito grande (máx. {MAX_REGULATION_BYTES // (1024 * 1024)} MB)."
        )
    if not data.startswith(b"%PDF"):
        raise RegulationError("Arquivo não é um PDF válido.")


def latest_version(db: Session, promo_id: int) -> int:
    current = (
        db.query(func.max(PromoRegulationVersion.version))
        .filter(PromoRegulationVersion.promo_id == promo_id)
        .scalar()
    )
    return int(current or 0)


def list_versions(db: Session, promo_id: int) -> list[PromoRegulationVersion]:
    return (
        db.query(PromoRegulationVersion)
        .filter(PromoRegulationVersion.promo_id == promo_id)
        .order_by(PromoRegulationVersion.version.desc())
        .all()
    )


def get_version(db: Session, promo_id: int, version: int) -> PromoRegulationVersion | None:
    return (
        db.query(PromoRegulationVersion)
        .filter(
            PromoRegulationVersion.promo_id == promo_id,
            PromoRegulationVersion.version == version,
        )
        .one_or_none()
    )


def store_regulation(
    db: Session,
    action: PromoAction,
    data: bytes,
    content_type: str | None,
    *,
    uploaded_by: User | None,
) -> PromoRegulationVersion:
    """Persist a new regulation version, keeping every previous file on disk."""
    validate_pdf(data, content_type)

    version = latest_version(db, action.id) + 1
    stored_name = f"v{version}.pdf"
    target = regulation_path(action.id, stored_name)

    row = PromoRegulationVersion(
        promo_id=action.id,
        version=version,
        stored_name=stored_name,
        uploaded_by_user_id=uploaded_by.id if uploaded_by is not None else None,
        uploaded_at=datetime.utcnow(),
    )
    db.add(row)
    action.regulation_version = version
    db.flush()

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_bytes(data)
        db.commit()
    except Exception:
        db.rollback()
        target.unlink(missing_ok=True)
        raise
    db.refresh(row)
    db.refresh(action)
    return row
