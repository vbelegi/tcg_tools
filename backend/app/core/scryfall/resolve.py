"""Resolve card names against Scryfall with DB cache."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.deck_import.plain_text import normalize_card_name
from app.core.scryfall.client import (
    UNRESOLVED,
    fetch_collection_by_names,
    pick_back_image_uris,
    pick_back_printed_name,
    pick_image_uris,
    pick_type_line,
)
from app.core.scryfall.types import type_category_from_type_line
from app.db.session import SessionLocal
from app.models import ScryfallCardCache

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedCard:
    name: str
    name_key: str
    found: bool
    scryfall_id: str | None
    printed_name: str | None
    printed_name_back: str | None
    type_line: str | None
    type_category: str
    layout: str | None
    image_normal: str | None
    image_small: str | None
    image_large: str | None
    image_normal_back: str | None
    image_small_back: str | None
    image_large_back: str | None


def _row_needs_refresh(row: ScryfallCardCache | None, *, name_key: str = "") -> bool:
    """True when missing entirely, or found but incomplete metadata (legacy cache)."""
    if row is None:
        return True
    if not row.found:
        # Retry false misses for split/adventure names — collection rejects "A // B".
        if " // " in (name_key or row.name_key or ""):
            return True
        return False
    if not row.type_line:
        return True
    if row.image_normal and not row.image_large:
        return True
    if row.found and not row.image_normal:
        return True
    # One-time back-face / layout fill for multi-face names (Adventure, MDFC, …).
    if row.layout is None and (
        " // " in (name_key or row.name_key or "")
        or (row.type_line and "//" in row.type_line)
        or (row.printed_name and " // " in row.printed_name)
    ):
        return True
    return False


def _apply_card(key: str, card: dict[str, Any], *, now: datetime) -> ScryfallCardCache:
    normal, small, large = pick_image_uris(card)
    back_n, back_s, back_l = pick_back_image_uris(card)
    layout = (card.get("layout") or "").strip() or None
    return ScryfallCardCache(
        name_key=key,
        found=True,
        scryfall_id=card.get("id"),
        printed_name=card.get("name"),
        printed_name_back=pick_back_printed_name(card),
        type_line=pick_type_line(card),
        layout=layout,
        image_normal=normal,
        image_small=small,
        image_large=large,
        image_normal_back=back_n,
        image_small_back=back_s,
        image_large_back=back_l,
        fetched_at=now,
    )


def _apply_miss(key: str, *, now: datetime) -> ScryfallCardCache:
    return ScryfallCardCache(
        name_key=key,
        found=False,
        scryfall_id=None,
        printed_name=None,
        printed_name_back=None,
        type_line=None,
        layout=None,
        image_normal=None,
        image_small=None,
        image_large=None,
        image_normal_back=None,
        image_small_back=None,
        image_large_back=None,
        fetched_at=now,
    )


def _empty_resolved(name: str, key: str) -> ResolvedCard:
    return ResolvedCard(
        name=name,
        name_key=key,
        found=False,
        scryfall_id=None,
        printed_name=None,
        printed_name_back=None,
        type_line=None,
        type_category="other",
        layout=None,
        image_normal=None,
        image_small=None,
        image_large=None,
        image_normal_back=None,
        image_small_back=None,
        image_large_back=None,
    )


def resolve_card_names(db: Session, names: list[str]) -> dict[str, ResolvedCard]:
    """
    Return ResolvedCard keyed by original name string.

    - Fills cache for unknown names.
    - Re-fetches incomplete rows (e.g. pre-020 without type_line).
    - If Scryfall is down / batch fails: keep existing cache; do not write false misses.
    """
    cleaned = [n for n in names if (n or "").strip()]
    if not cleaned:
        return {}

    keys = {n: normalize_card_name(n) for n in cleaned}
    unique_keys = list(dict.fromkeys(keys.values()))

    cached: dict[str, ScryfallCardCache] = {
        row.name_key: row
        for row in db.query(ScryfallCardCache)
        .filter(ScryfallCardCache.name_key.in_(unique_keys))
        .all()
    }

    to_fetch: list[str] = []
    fetch_keys: set[str] = set()
    for name, key in keys.items():
        if key in fetch_keys:
            continue
        if _row_needs_refresh(cached.get(key), name_key=key):
            fetch_keys.add(key)
            to_fetch.append(name)

    if to_fetch:
        fetched = fetch_collection_by_names(to_fetch)
        now = datetime.utcnow()
        dirty = False
        for name in to_fetch:
            key = normalize_card_name(name)
            existing = cached.get(key)
            payload = fetched.get(name, UNRESOLVED)

            if payload is UNRESOLVED:
                # Transport / API failure — keep whatever we already have.
                logger.debug("scryfall unresolved for %r; keeping cache", name)
                continue

            if isinstance(payload, dict):
                row = _apply_card(key, payload, now=now)
                db.merge(row)
                cached[key] = row
                dirty = True
                continue

            # Definitive not_found (None).
            if existing is not None and existing.found:
                # Keep images/meta from a prior successful resolve; retry later.
                logger.info(
                    "scryfall not_found for cached hit %r; keeping existing row",
                    name,
                )
                continue

            row = _apply_miss(key, now=now)
            db.merge(row)
            cached[key] = row
            dirty = True

        if dirty:
            try:
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("scryfall cache commit failed")

    out: dict[str, ResolvedCard] = {}
    for name, key in keys.items():
        row = cached.get(key)
        if row is None:
            out[name] = _empty_resolved(name, key)
            continue
        type_line = row.type_line
        out[name] = ResolvedCard(
            name=name,
            name_key=key,
            found=bool(row.found),
            scryfall_id=row.scryfall_id,
            printed_name=row.printed_name,
            printed_name_back=row.printed_name_back,
            type_line=type_line,
            type_category=type_category_from_type_line(type_line),
            layout=row.layout,
            image_normal=row.image_normal,
            image_small=row.image_small,
            image_large=row.image_large,
            image_normal_back=row.image_normal_back,
            image_small_back=row.image_small_back,
            image_large_back=row.image_large_back,
        )
    return out


def warm_card_names(names: list[str]) -> None:
    """Background-friendly warmer: own DB session."""
    if not names:
        return
    db = SessionLocal()
    try:
        resolve_card_names(db, names)
    except Exception:
        logger.exception("scryfall warm failed")
    finally:
        db.close()
