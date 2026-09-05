"""Minimal Scryfall HTTP client (collection batch)."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SCRYFALL_COLLECTION = "https://api.scryfall.com/cards/collection"
USER_AGENT = "TCGTools/1.17.0 (+https://github.com/vbelegi/tcg_tools; scryfall-cache)"
BATCH_SIZE = 75
# Collection hard limit is 2/sec; leave headroom.
BATCH_GAP_SEC = 0.55
TIMEOUT_SEC = 20.0

# Sentinel: batch failed / never got a definitive Scryfall answer for this name.
UNRESOLVED = object()


def scryfall_query_name(name: str) -> str:
    """
    Name to send to /cards/collection.

    Adventure / MDFC / split-style names are stored as "Front // Back", but the
    collection `name` identifier often only accepts the front face.
    """
    raw = (name or "").strip()
    if " // " in raw:
        front = raw.split(" // ", 1)[0].strip()
        return front or raw
    return raw


def fetch_collection_by_names(
    names: list[str],
    *,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """
    Resolve exact English names via /cards/collection.

    Returns map of requested name ->:
      - card JSON dict on hit
      - None on definitive not_found
      - UNRESOLVED if the HTTP/batch failed (caller must not cache as miss)

    For "Front // Back" deck lines, queries Scryfall with the front face only.
    """
    result: dict[str, Any] = {n: UNRESOLVED for n in names}
    if not names:
        return result

    owns = client is None
    http = client or httpx.Client(timeout=TIMEOUT_SEC, follow_redirects=True)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        for i in range(0, len(names), BATCH_SIZE):
            if i > 0:
                time.sleep(BATCH_GAP_SEC)
            batch = names[i : i + BATCH_SIZE]
            payload = {"identifiers": [{"name": scryfall_query_name(n)} for n in batch]}
            try:
                resp = http.post(SCRYFALL_COLLECTION, headers=headers, json=payload)
            except httpx.HTTPError as exc:
                logger.warning("scryfall collection failed: %s", exc)
                continue
            if resp.status_code == 429:
                logger.warning("scryfall rate limited; backing off")
                time.sleep(30)
                try:
                    resp = http.post(SCRYFALL_COLLECTION, headers=headers, json=payload)
                except httpx.HTTPError:
                    continue
            if resp.status_code >= 400:
                logger.warning("scryfall HTTP %s", resp.status_code)
                continue
            try:
                data = resp.json()
            except ValueError:
                logger.warning("scryfall invalid JSON")
                continue
            by_lower: dict[str, dict[str, Any]] = {}
            for card in data.get("data") or []:
                for key in _card_name_keys(card):
                    by_lower[key] = card
            not_found_q = {
                (m.get("name") or "").strip().lower()
                for m in (data.get("not_found") or [])
                if (m.get("name") or "").strip()
            }
            for name in batch:
                q = scryfall_query_name(name)
                card = by_lower.get(name.strip().lower()) or by_lower.get(q.strip().lower())
                if card is not None:
                    result[name] = card
                elif name.strip().lower() in not_found_q or q.strip().lower() in not_found_q:
                    result[name] = None
                else:
                    # Successful HTTP but unmatched — treat as miss for this identifier.
                    result[name] = None
    finally:
        if owns:
            http.close()
    return result


def _card_name_keys(card: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    name = (card.get("name") or "").strip().lower()
    if name:
        keys.append(name)
        if " // " in name:
            keys.append(name.split(" // ", 1)[0].strip())
    for face in card.get("card_faces") or []:
        fname = (face.get("name") or "").strip().lower()
        if fname and fname not in keys:
            keys.append(fname)
    return keys


def pick_image_uris(card: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Return (normal, small, large) image URLs for the front face."""
    uris = card.get("image_uris")
    if isinstance(uris, dict):
        return uris.get("normal"), uris.get("small"), uris.get("large")
    faces = card.get("card_faces") or []
    if faces and isinstance(faces[0], dict):
        furis = faces[0].get("image_uris") or {}
        if isinstance(furis, dict):
            return furis.get("normal"), furis.get("small"), furis.get("large")
    return None, None, None


def pick_back_image_uris(card: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """
    Return (normal, small, large) for the back face when it has its own art.

    True DFCs / MDFCs / battles expose image_uris on card_faces[1].
    Adventures and most splits do not — returns (None, None, None).
    """
    faces = card.get("card_faces") or []
    if len(faces) < 2 or not isinstance(faces[1], dict):
        return None, None, None
    furis = faces[1].get("image_uris") or {}
    if not isinstance(furis, dict) or not furis.get("normal"):
        return None, None, None
    return furis.get("normal"), furis.get("small"), furis.get("large")


def pick_back_printed_name(card: dict[str, Any]) -> str | None:
    """Back-face printed name when the card is flippable (has back art)."""
    normal, _, _ = pick_back_image_uris(card)
    if not normal:
        return None
    faces = card.get("card_faces") or []
    if len(faces) < 2 or not isinstance(faces[1], dict):
        return None
    name = (faces[1].get("name") or "").strip()
    return name or None


def pick_type_line(card: dict[str, Any]) -> str | None:
    tl = (card.get("type_line") or "").strip()
    if tl:
        return tl
    faces = card.get("card_faces") or []
    parts: list[str] = []
    for face in faces:
        if not isinstance(face, dict):
            continue
        ftl = (face.get("type_line") or "").strip()
        if ftl:
            parts.append(ftl)
    if parts:
        return " // ".join(parts)
    return None
