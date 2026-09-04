"""Unit tests for plain-text decklist parsing."""

from app.core.deck_import.plain_text import parse_plain_decklist, unique_card_names


def test_parse_plain_decklist_sections():
    text = """Commander
1 Atraxa, Praetors' Voice

Deck
4 Path to Exile
2 Sol Ring

Sideboard
1 Swords to Plowshares
"""
    lines = parse_plain_decklist(text)
    assert [(l.section, l.qty, l.name) for l in lines] == [
        ("commander", 1, "Atraxa, Praetors' Voice"),
        ("main", 4, "Path to Exile"),
        ("main", 2, "Sol Ring"),
        ("sideboard", 1, "Swords to Plowshares"),
    ]


def test_unique_card_names_dedupes():
    lines = parse_plain_decklist("Deck\n2 Sol Ring\n1 Sol Ring\n")
    assert unique_card_names(lines) == ["Sol Ring"]
