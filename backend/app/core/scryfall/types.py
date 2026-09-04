"""Derive deck-display type categories from Scryfall type_line."""

from __future__ import annotations

# Display order for main/sideboard subgroups.
TYPE_CATEGORY_ORDER = (
    "creatures",
    "planeswalkers",
    "battles",
    "instants",
    "sorceries",
    "artifacts",
    "enchantments",
    "lands",
    "other",
)

TYPE_CATEGORY_LABELS = {
    "creatures": "Creatures",
    "planeswalkers": "Planeswalkers",
    "battles": "Battles",
    "instants": "Instants",
    "sorceries": "Sorceries",
    "artifacts": "Artifacts",
    "enchantments": "Enchantments",
    "lands": "Lands",
    "other": "Other",
}


def type_category_from_type_line(type_line: str | None) -> str:
    """
    Map Scryfall type_line to a grouping key.

    Order of checks matters for dual types (e.g. Artifact Creature → creatures).
    """
    if not type_line:
        return "other"
    # Use the face before // for DFCs.
    primary = type_line.split("//", 1)[0].strip().lower()
    # Drop subtypes after em dash or hyphen used by Scryfall ("Creature — Elf").
    for sep in ("—", "–", "-"):
        if sep in primary:
            primary = primary.split(sep, 1)[0].strip()
            break

    if "creature" in primary:
        return "creatures"
    if "planeswalker" in primary:
        return "planeswalkers"
    if "battle" in primary:
        return "battles"
    if "instant" in primary:
        return "instants"
    if "sorcery" in primary:
        return "sorceries"
    if "land" in primary:
        return "lands"
    if "artifact" in primary:
        return "artifacts"
    if "enchantment" in primary:
        return "enchantments"
    return "other"
