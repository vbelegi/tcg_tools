"""Unit tests for LigaMagic deck import (Magic EN)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.core.deck_import.ligamagic import (
    DeckImportError,
    canonical_en_url,
    extract_deck_id,
    parse_brl_price,
    parse_ligamagic_html,
)

FIXTURE = Path(__file__).parent / "fixtures" / "ligamagic" / "deck_10187992_en_min.html"


def test_extract_deck_id_from_pt_or_en_url():
    assert (
        extract_deck_id(
            "https://www.ligamagic.com.br/?view=dks/deck&id=10187992&lang=1#10187992"
        )
        == "10187992"
    )
    assert (
        extract_deck_id("https://www.ligamagic.com.br/?view=dks/deck&id=10187992")
        == "10187992"
    )


def test_extract_deck_id_rejects_foreign_host():
    with pytest.raises(DeckImportError, match="LigaMagic"):
        extract_deck_id("https://example.com/?id=1")


def test_canonical_en_url_forces_lang_2():
    assert "lang=2" in canonical_en_url("10187992")
    assert "id=10187992" in canonical_en_url("10187992")


def test_parse_brl_price():
    assert parse_brl_price("R$ 493,17") == Decimal("493.17")
    assert parse_brl_price("1.471,71") == Decimal("1471.71")


def test_parse_fixture_snapshot():
    html = FIXTURE.read_text(encoding="utf-8")
    snap = parse_ligamagic_html(
        html,
        deck_id="10187992",
        source_url=canonical_en_url("10187992"),
    )
    assert snap.source == "ligamagic"
    assert snap.source_deck_id == "10187992"
    assert snap.name == "Momo_clm17_etapa2"
    assert snap.format == "Duel Commander"
    assert snap.price_low_brl == Decimal("493.17")
    assert snap.price_currency == "BRL"
    assert snap.card_count == 100
    assert "Commander" in snap.plain_text
    assert "1 Momo, Friendly Flier" in snap.plain_text
    assert "1 Giver of Runes" in snap.plain_text
    assert "30 Snow-Covered Plains" in snap.plain_text
    assert "Path to Exile" in snap.plain_text
    assert "Maybeboard" not in snap.plain_text
    assert "Sheltered by Ghosts" not in snap.plain_text
