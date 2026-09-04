"""Fetch + parse LigaMagic decks for preview."""

from __future__ import annotations

import logging

import httpx

from app.core.deck_import.ligamagic import (
    DeckImportError,
    LigaMagicDeckSnapshot,
    canonical_en_url,
    extract_deck_id,
    parse_ligamagic_html,
)

logger = logging.getLogger(__name__)

USER_AGENT = "TCGTools/1.16.1 (+https://github.com/vbelegi/tcg_tools; deck-import)"
FETCH_TIMEOUT_SEC = 15.0


def import_ligamagic_preview(url: str, *, client: httpx.Client | None = None) -> LigaMagicDeckSnapshot:
    deck_id = extract_deck_id(url)
    source_url = canonical_en_url(deck_id)
    html = _fetch_en_html(source_url, client=client)
    return parse_ligamagic_html(html, deck_id=deck_id, source_url=source_url)


def _fetch_en_html(source_url: str, *, client: httpx.Client | None = None) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Cookie": "dk-language=2",
    }
    owns_client = client is None
    http = client or httpx.Client(timeout=FETCH_TIMEOUT_SEC, follow_redirects=True)
    try:
        resp = http.get(source_url, headers=headers)
        if resp.status_code >= 400:
            raise DeckImportError(
                f"LigaMagic respondeu HTTP {resp.status_code}. Tente de novo ou cole a lista manualmente."
            )
        return resp.text
    except httpx.TimeoutException as exc:
        raise DeckImportError("Tempo esgotado ao consultar a LigaMagic.") from exc
    except httpx.HTTPError as exc:
        logger.warning("ligamagic fetch failed: %s", exc)
        raise DeckImportError("Falha de rede ao consultar a LigaMagic.") from exc
    finally:
        if owns_client:
            http.close()
