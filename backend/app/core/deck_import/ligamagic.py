"""LigaMagic deck import — Magic EN snapshot (plain text + low price)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from html import unescape
from urllib.parse import parse_qs, unquote_plus, urlparse

ALLOWED_HOSTS = frozenset({"www.ligamagic.com.br", "ligamagic.com.br"})
EN_LANG = "2"
CANONICAL_URL = "https://www.ligamagic.com.br/?view=dks/deck&id={id}&lang={lang}"

SECTION_COMMANDER = frozenset({"comandante", "commander"})
SECTION_SIDEBOARD = frozenset({"sideboard", "side board", "reserva", "side", "sb"})
SECTION_MAYBE = frozenset({"maybeboard", "maybe board", "considerados"})
# Alternate page views that re-list the same cards (by color / rarity).
SECTION_ALT_VIEW = frozenset(
    {
        "branco",
        "white",
        "azul",
        "blue",
        "preto",
        "black",
        "vermelho",
        "red",
        "verde",
        "green",
        "multicolor",
        "multicolour",
        "incolor",
        "colorless",
        "comum",
        "common",
        "incomum",
        "uncommon",
        "rara",
        "rare",
        "mítica",
        "mitica",
        "mythic",
        "mythic rare",
    }
)
# Back-compat alias used in older comments/tests.
SECTION_STOP_REPEAT = SECTION_ALT_VIEW


class DeckImportError(ValueError):
    """Invalid URL or unparseable LigaMagic deck page."""


@dataclass(frozen=True)
class DeckLine:
    qty: int
    name: str
    section: str  # commander | main | sideboard


@dataclass
class LigaMagicDeckSnapshot:
    source: str
    source_deck_id: str
    source_url: str
    name: str | None
    format: str | None
    plain_text: str
    lines: list[DeckLine]
    price_low_brl: Decimal | None
    price_currency: str
    warnings: list[str] = field(default_factory=list)

    @property
    def card_count(self) -> int:
        return sum(line.qty for line in self.lines)


def extract_deck_id(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        raise DeckImportError("Informe a URL do deck na LigaMagic.")
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise DeckImportError("URL deve ser da LigaMagic (ligamagic.com.br).")
    qs = parse_qs(parsed.query)
    ids = qs.get("id") or []
    if not ids or not ids[0].isdigit():
        raise DeckImportError("Não foi possível extrair o id do deck na URL.")
    return ids[0]


def canonical_en_url(deck_id: str) -> str:
    return CANONICAL_URL.format(id=deck_id, lang=EN_LANG)


def parse_brl_price(raw: str) -> Decimal:
    s = raw.strip().replace("R$", "").replace("\xa0", "").strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation as exc:
        raise DeckImportError(f"Preço inválido: {raw!r}") from exc


def _section_kind(header: str) -> str | None:
    base = header.split("(")[0].strip().casefold()
    if not base:
        return None
    if base in SECTION_MAYBE or base.startswith("maybe"):
        return "maybe"
    if "cards total" in base:
        # Main listing finished; Sideboard usually follows on LigaMagic.
        return "cards_total"
    if base.startswith("cmc"):
        return "alt_view"
    if base in SECTION_ALT_VIEW:
        return "alt_view"
    if base in SECTION_COMMANDER:
        return "commander"
    if base in SECTION_SIDEBOARD:
        return "sideboard"
    # Criaturas / Mágicas / Artefatos / Encantamentos / Terrenos / Deck …
    return "main"


def parse_ligamagic_html(
    html: str,
    *,
    deck_id: str,
    source_url: str,
) -> LigaMagicDeckSnapshot:
    text = html or ""
    warnings: list[str] = []

    name: str | None = None
    m_title = re.search(r'<span class="lj b">([^<]+)</span>', text)
    if m_title:
        name = unescape(m_title.group(1)).strip() or None
    if name is None:
        m_cmt = re.search(r"<!--\s*title:([^>]+)-->", text)
        if m_cmt:
            name = m_cmt.group(1).strip() or None

    fmt: str | None = None
    m_fmt = re.search(r"filtro_formato=\d+['\"]?>([^<]+)</a>", text)
    if m_fmt:
        fmt = unescape(m_fmt.group(1)).strip() or None
    if fmt is None:
        m_cmt = re.search(r"<!--\s*format:([^>]+)-->", text)
        if m_cmt:
            fmt = m_cmt.group(1).strip() or None

    price_low: Decimal | None = None
    m_price = re.search(
        r"class=['\"]price-head lower[^'\"]*['\"][^>]*>\s*R\$\s*([^<]+)",
        text,
    )
    if m_price:
        try:
            price_low = parse_brl_price(m_price.group(1))
        except DeckImportError:
            warnings.append("Não foi possível interpretar o preço menor da Liga.")
    else:
        warnings.append("Preço menor (verde) não encontrado na página.")

    lines: list[DeckLine] = []
    current = "main"
    seen_cards_total = False

    pattern = re.compile(
        r"<div class='deck-type[^']*'>(.*?)</div>"
        r"|<div class='deck-qty'>(.*?)</div>\s*"
        r"<div class='deck-card'>\s*<a[^>]*href=\"/\?view=cards/card&card=([^\"]+)\"[^>]*>(.*?)</a>",
        re.I | re.S,
    )

    for m in pattern.finditer(text):
        if m.group(1) is not None:
            header = re.sub(r"<[^>]+>", "", unescape(m.group(1))).strip()
            kind = _section_kind(header)
            if kind == "maybe":
                warnings.append("Maybeboard ignorado no snapshot.")
                break
            if kind == "cards_total":
                seen_cards_total = True
                continue
            if kind == "alt_view":
                # Color / CMC / rarity blocks re-list the same cards after the
                # primary type listing (and usually after Sideboard).
                if seen_cards_total or current == "sideboard":
                    break
                current = "main"
                continue
            if kind in {"commander", "sideboard", "main"}:
                current = kind
            continue

        qty_raw = unescape(m.group(2) or "").replace("\xa0", " ").strip()
        qty_m = re.match(r"(\d+)", qty_raw)
        if not qty_m:
            continue
        qty = int(qty_m.group(1))
        href_name = unquote_plus(m.group(3) or "").strip()
        anchor = re.sub(r"<[^>]+>", "", unescape(m.group(4) or "")).strip()
        card_name = href_name or anchor
        if not card_name:
            continue
        lines.append(DeckLine(qty=qty, name=card_name, section=current))

    if not lines:
        raise DeckImportError("Não foi possível ler as cartas do deck (HTML inesperado).")

    return LigaMagicDeckSnapshot(
        source="ligamagic",
        source_deck_id=str(deck_id),
        source_url=source_url,
        name=name,
        format=fmt,
        plain_text=_to_plain_text(lines),
        lines=lines,
        price_low_brl=price_low,
        price_currency="BRL",
        warnings=warnings,
    )


def _to_plain_text(lines: list[DeckLine]) -> str:
    chunks: list[str] = []
    order = ("commander", "main", "sideboard")
    labels = {"commander": "Commander", "main": "Deck", "sideboard": "Sideboard"}
    by_sec: dict[str, list[DeckLine]] = {k: [] for k in order}
    for line in lines:
        by_sec.setdefault(line.section, []).append(line)
    for sec in order:
        items = by_sec.get(sec) or []
        if not items:
            continue
        chunks.append(labels[sec])
        for item in items:
            chunks.append(f"{item.qty} {item.name}")
        chunks.append("")
    return "\n".join(chunks).strip() + "\n"
