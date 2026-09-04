from __future__ import annotations

import re
from pathlib import Path

src = Path("tests/unit/fixtures/ligamagic/deck_10187992_en.html")
text = src.read_text(encoding="utf-8", errors="replace")

# Isolate the three price heads
m = re.search(
    r"(<div[^>]*id='prices-2-10187992'[^>]*>R\$\s*493,17</div>)",
    text,
)
price_block = (
    "<div class='price-heads'>"
    "<div title='Menor' id='prices-2-10187992' class='price-head lower price-selected'>R$ 493,17</div>"
    "<div title='Medio' id='prices-3-10187992' class='price-head medium '>R$ 1.471,71</div>"
    "<div title='Maior' id='prices-4-10187992' class='price-head higher '>R$ 12.198,71</div>"
    "</div>"
)
if m:
    print("found live price node")

fmt = re.search(r"filtro_formato=\d+'>([^<]+)</a></div><div class='createdby'", text)
title = re.search(r'<span class="lj b">([^<]+)</span>', text)
start = text.find("<div class='deck-line'><div class='deck-type deck-type-first'>Comandante")
mb = text.find("Maybeboard", start)
end = text.find("deck-type deck-type-first'>Branco", mb)
chunk = text[start:end]

parts = [
    "<!DOCTYPE html><html><body>",
    f"<!-- title:{title.group(1) if title else 'Deck'} -->",
    f"<!-- format:{fmt.group(1) if fmt else 'Unknown'} -->",
    price_block,
    "<div class='dck-main'>",
    chunk,
    "</div></body></html>",
]
out = Path("tests/unit/fixtures/ligamagic/deck_10187992_en_min.html")
out.write_text("\n".join(parts) + "\n", encoding="utf-8")
print("bytes", out.stat().st_size, "has price", "493,17" in out.read_text(encoding="utf-8"))
