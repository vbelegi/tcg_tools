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


def test_parse_keeps_sideboard_after_color_and_total_headers():
    """Type listing + cards total + Sideboard; alt views after must not duplicate."""
    html = """
    <span class="lj b">Test Deck</span>
    <a href="?filtro_formato=1">Duel Commander</a>
    <div class='price-head lower'>R$ 10,00</div>
    <div class='deck-type'>Comandante <i>(1)</i></div>
    <div class='deck-qty'>1&nbsp;</div><div class='deck-card'><a href="/?view=cards/card&card=Sol%20Ring">Sol Ring</a>
    <div class='deck-type'>Criaturas <i>(1)</i></div>
    <div class='deck-qty'>1&nbsp;</div><div class='deck-card'><a href="/?view=cards/card&card=Birds%20of%20Paradise">Birds of Paradise</a>
    <div class='deck-type'>White</div>
    <div class='deck-qty'>1&nbsp;</div><div class='deck-card'><a href="/?view=cards/card&card=Plains">Plains</a>
    <div class='deck-type'>60 cards total</div>
    <div class='deck-type'>Sideboard <i>(2)</i></div>
    <div class='deck-qty'>1&nbsp;</div><div class='deck-card'><a href="/?view=cards/card&card=Swords%20to%20Plowshares">Swords to Plowshares</a>
    <div class='deck-qty'>1&nbsp;</div><div class='deck-card'><a href="/?view=cards/card&card=Path%20to%20Exile">Path to Exile</a>
    <div class='deck-type'>Azul <i>(41)</i></div>
    <div class='deck-qty'>4&nbsp;</div><div class='deck-card'><a href="/?view=cards/card&card=Counterspell">Counterspell</a>
    <div class='deck-type'>Maybeboard <i>(1)</i></div>
    <div class='deck-qty'>1&nbsp;</div><div class='deck-card'><a href="/?view=cards/card&card=Ignore%20Me">Ignore Me</a>
    """
    snap = parse_ligamagic_html(html, deck_id="1", source_url=canonical_en_url("1"))
    by_sec: dict[str, list[str]] = {}
    for line in snap.lines:
        by_sec.setdefault(line.section, []).append(line.name)
    assert by_sec.get("commander") == ["Sol Ring"]
    assert by_sec.get("main") == ["Birds of Paradise", "Plains"]
    assert by_sec.get("sideboard") == ["Swords to Plowshares", "Path to Exile"]
    assert snap.card_count == 5
    assert "Counterspell" not in snap.plain_text
    assert "Ignore Me" not in snap.plain_text
    assert "Sideboard" in snap.plain_text
