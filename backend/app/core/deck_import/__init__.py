"""Deck import adapters (LigaMagic Magic EN first)."""

from __future__ import annotations

from app.core.deck_import.ligamagic import (
    DeckImportError,
    DeckLine,
    LigaMagicDeckSnapshot,
    canonical_en_url,
    extract_deck_id,
    parse_ligamagic_html,
)
from app.core.deck_import.plain_text import parse_plain_decklist, unique_card_names
from app.core.deck_import.service import import_ligamagic_preview

__all__ = [
    "DeckImportError",
    "DeckLine",
    "LigaMagicDeckSnapshot",
    "canonical_en_url",
    "extract_deck_id",
    "import_ligamagic_preview",
    "parse_ligamagic_html",
    "parse_plain_decklist",
    "unique_card_names",
]
