"""Unit tests for Scryfall image URI helpers + resolve cache + type categories."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from app.core.scryfall.client import UNRESOLVED, pick_image_uris, pick_type_line
from app.core.scryfall.resolve import resolve_card_names
from app.core.scryfall.types import type_category_from_type_line
from app.models import ScryfallCardCache


def test_pick_image_uris_normal():
    normal, small, large = pick_image_uris(
        {
            "image_uris": {
                "normal": "https://n.example/n.jpg",
                "small": "https://n.example/s.jpg",
                "large": "https://n.example/l.jpg",
            }
        }
    )
    assert normal.endswith("n.jpg")
    assert small.endswith("s.jpg")
    assert large.endswith("l.jpg")


def test_pick_image_uris_dfc():
    normal, small, large = pick_image_uris(
        {
            "card_faces": [
                {
                    "image_uris": {
                        "normal": "https://n.example/front.jpg",
                        "small": "https://n.example/fs.jpg",
                        "large": "https://n.example/fl.jpg",
                    }
                }
            ]
        }
    )
    assert normal.endswith("front.jpg")
    assert large.endswith("fl.jpg")


def test_pick_back_image_uris_mdfc():
    from app.core.scryfall.client import pick_back_image_uris, pick_back_printed_name

    card = {
        "layout": "modal_dfc",
        "name": "Razorgrass Ambush // Razorgrass Field",
        "card_faces": [
            {
                "name": "Razorgrass Ambush",
                "image_uris": {
                    "normal": "https://n.example/front.jpg",
                    "small": "https://n.example/fs.jpg",
                    "large": "https://n.example/fl.jpg",
                },
            },
            {
                "name": "Razorgrass Field",
                "image_uris": {
                    "normal": "https://n.example/back.jpg",
                    "small": "https://n.example/bs.jpg",
                    "large": "https://n.example/bl.jpg",
                },
            },
        ],
    }
    bn, bs, bl = pick_back_image_uris(card)
    assert bn.endswith("back.jpg")
    assert bl.endswith("bl.jpg")
    assert pick_back_printed_name(card) == "Razorgrass Field"


def test_pick_back_image_uris_adventure_none():
    from app.core.scryfall.client import pick_back_image_uris, pick_back_printed_name

    card = {
        "layout": "adventure",
        "name": "Bonecrusher Giant // Stomp",
        "image_uris": {
            "normal": "https://n.example/bone.jpg",
            "small": "https://n.example/bone-s.jpg",
            "large": "https://n.example/bone-l.jpg",
        },
        "card_faces": [
            {"name": "Bonecrusher Giant"},
            {"name": "Stomp"},
        ],
    }
    assert pick_back_image_uris(card) == (None, None, None)
    assert pick_back_printed_name(card) is None


def test_pick_type_line_from_face():
    assert pick_type_line({"card_faces": [{"type_line": "Creature — Human"}]}) == "Creature — Human"


def test_type_category_mapping():
    assert type_category_from_type_line("Creature — Elf Warrior") == "creatures"
    assert type_category_from_type_line("Artifact Creature — Construct") == "creatures"
    assert type_category_from_type_line("Instant") == "instants"
    assert type_category_from_type_line("Sorcery") == "sorceries"
    assert type_category_from_type_line("Artifact — Equipment") == "artifacts"
    assert type_category_from_type_line("Enchantment — Aura") == "enchantments"
    assert type_category_from_type_line("Basic Land — Plains") == "lands"
    assert type_category_from_type_line("Legendary Planeswalker — Jace") == "planeswalkers"
    assert type_category_from_type_line(None) == "other"


def test_resolve_uses_cache(db_session):
    db_session.add(
        ScryfallCardCache(
            name_key="sol ring",
            found=True,
            scryfall_id="abc",
            printed_name="Sol Ring",
            type_line="Artifact",
            image_normal="https://img/sol.jpg",
            image_small="https://img/sol-s.jpg",
            image_large="https://img/sol-l.jpg",
            fetched_at=datetime.utcnow(),
        )
    )
    db_session.commit()
    with patch("app.core.scryfall.resolve.fetch_collection_by_names") as mock_fetch:
        out = resolve_card_names(db_session, ["Sol Ring", "sol ring"])
        mock_fetch.assert_not_called()
    assert out["Sol Ring"].found is True
    assert out["Sol Ring"].image_normal == "https://img/sol.jpg"
    assert out["Sol Ring"].type_category == "artifacts"
    assert out["sol ring"].scryfall_id == "abc"


def test_resolve_refreshes_stale_type_line(db_session):
    db_session.add(
        ScryfallCardCache(
            name_key="sol ring",
            found=True,
            scryfall_id="abc",
            printed_name="Sol Ring",
            type_line=None,
            image_normal="https://img/sol.jpg",
            image_small="https://img/sol-s.jpg",
            image_large=None,
            fetched_at=datetime.utcnow(),
        )
    )
    db_session.commit()
    payload = {
        "Sol Ring": {
            "id": "abc",
            "name": "Sol Ring",
            "type_line": "Artifact",
            "image_uris": {
                "normal": "https://img/sol.jpg",
                "small": "https://img/sol-s.jpg",
                "large": "https://img/sol-l.jpg",
            },
        }
    }
    with patch("app.core.scryfall.resolve.fetch_collection_by_names", return_value=payload):
        out = resolve_card_names(db_session, ["Sol Ring"])
    assert out["Sol Ring"].type_category == "artifacts"
    assert out["Sol Ring"].image_large.endswith("sol-l.jpg")
    row = db_session.get(ScryfallCardCache, "sol ring")
    assert row is not None
    assert row.type_line == "Artifact"


def test_scryfall_query_name_strips_adventure_face():
    from app.core.scryfall.client import scryfall_query_name

    assert scryfall_query_name("Bonecrusher Giant // Stomp") == "Bonecrusher Giant"
    assert scryfall_query_name("Sol Ring") == "Sol Ring"


def test_resolve_retries_split_name_miss(db_session):
    db_session.add(
        ScryfallCardCache(
            name_key="bonecrusher giant // stomp",
            found=False,
            fetched_at=datetime.utcnow(),
        )
    )
    db_session.commit()
    payload = {
        "Bonecrusher Giant // Stomp": {
            "id": "clb-781",
            "name": "Bonecrusher Giant // Stomp",
            "type_line": "Creature — Giant // Instant — Adventure",
            "layout": "adventure",
            "image_uris": {
                "normal": "https://img/bone.jpg",
                "small": "https://img/bone-s.jpg",
                "large": "https://img/bone-l.jpg",
            },
        }
    }
    with patch("app.core.scryfall.resolve.fetch_collection_by_names", return_value=payload) as mock_fetch:
        out = resolve_card_names(db_session, ["Bonecrusher Giant // Stomp"])
        mock_fetch.assert_called_once()
    assert out["Bonecrusher Giant // Stomp"].found is True
    assert out["Bonecrusher Giant // Stomp"].image_normal == "https://img/bone.jpg"
    row = db_session.get(ScryfallCardCache, "bonecrusher giant // stomp")
    assert row is not None and row.found is True


def test_resolve_refreshes_layout_for_back_face(db_session):
    db_session.add(
        ScryfallCardCache(
            name_key="razorgrass ambush // razorgrass field",
            found=True,
            scryfall_id="mh3-1",
            printed_name="Razorgrass Ambush // Razorgrass Field",
            type_line="Instant // Land",
            layout=None,
            image_normal="https://img/front.jpg",
            image_small="https://img/fs.jpg",
            image_large="https://img/fl.jpg",
            fetched_at=datetime.utcnow(),
        )
    )
    db_session.commit()
    payload = {
        "Razorgrass Ambush // Razorgrass Field": {
            "id": "mh3-1",
            "name": "Razorgrass Ambush // Razorgrass Field",
            "layout": "modal_dfc",
            "type_line": "Instant // Land",
            "card_faces": [
                {
                    "name": "Razorgrass Ambush",
                    "image_uris": {
                        "normal": "https://img/front.jpg",
                        "small": "https://img/fs.jpg",
                        "large": "https://img/fl.jpg",
                    },
                },
                {
                    "name": "Razorgrass Field",
                    "image_uris": {
                        "normal": "https://img/back.jpg",
                        "small": "https://img/bs.jpg",
                        "large": "https://img/bl.jpg",
                    },
                },
            ],
        }
    }
    with patch("app.core.scryfall.resolve.fetch_collection_by_names", return_value=payload) as mock_fetch:
        out = resolve_card_names(db_session, ["Razorgrass Ambush // Razorgrass Field"])
        mock_fetch.assert_called_once()
    card = out["Razorgrass Ambush // Razorgrass Field"]
    assert card.image_normal_back.endswith("back.jpg")
    assert card.printed_name_back == "Razorgrass Field"
    assert card.layout == "modal_dfc"
    row = db_session.get(ScryfallCardCache, "razorgrass ambush // razorgrass field")
    assert row is not None
    assert row.layout == "modal_dfc"
    assert row.image_normal_back.endswith("back.jpg")


def test_resolve_keeps_cache_when_scryfall_unresolved(db_session):
    db_session.add(
        ScryfallCardCache(
            name_key="sol ring",
            found=True,
            scryfall_id="abc",
            printed_name="Sol Ring",
            type_line=None,
            image_normal="https://img/sol.jpg",
            image_small="https://img/sol-s.jpg",
            fetched_at=datetime.utcnow(),
        )
    )
    db_session.commit()
    with patch(
        "app.core.scryfall.resolve.fetch_collection_by_names",
        return_value={"Sol Ring": UNRESOLVED},
    ):
        out = resolve_card_names(db_session, ["Sol Ring"])
    assert out["Sol Ring"].found is True
    assert out["Sol Ring"].image_normal == "https://img/sol.jpg"
    assert out["Sol Ring"].type_category == "other"
    row = db_session.get(ScryfallCardCache, "sol ring")
    assert row is not None
    assert row.found is True
    assert row.image_normal == "https://img/sol.jpg"
