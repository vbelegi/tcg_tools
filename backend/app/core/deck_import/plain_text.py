"""Parse stored plain-text decklists (LigaMagic snapshot shape)."""

from __future__ import annotations

import re

from app.core.deck_import.ligamagic import DeckLine

_SECTION_MAP = {
    "commander": "commander",
    "comandante": "commander",
    "deck": "main",
    "main": "main",
    "mainboard": "main",
    "main board": "main",
    "sideboard": "sideboard",
    "side board": "sideboard",
    "side": "sideboard",
    "reserva": "sideboard",
}

_LINE_RE = re.compile(r"^(\d+)\s+(.+)$")


def parse_plain_decklist(text: str | None) -> list[DeckLine]:
    """Parse qty/name lines with optional section headers into DeckLine list."""
    if not text or not text.strip():
        return []
    section = "main"
    out: list[DeckLine] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        key = line.lower()
        if key in _SECTION_MAP:
            section = _SECTION_MAP[key]
            continue
        m = _LINE_RE.match(line)
        if not m:
            continue
        qty = int(m.group(1))
        name = m.group(2).strip()
        if qty < 1 or not name:
            continue
        out.append(DeckLine(qty=qty, name=name, section=section))
    return out


def unique_card_names(lines: list[DeckLine]) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for line in lines:
        key = normalize_card_name(line.name)
        if key in seen:
            continue
        seen.add(key)
        names.append(line.name)
    return names


def normalize_card_name(name: str) -> str:
    return " ".join((name or "").strip().lower().split())
