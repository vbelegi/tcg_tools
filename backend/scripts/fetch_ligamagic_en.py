from __future__ import annotations

import re
import urllib.request
from pathlib import Path

url = "https://www.ligamagic.com.br/?view=dks/deck&id=10187992&lang=2"
req = urllib.request.Request(
    url,
    headers={
        "User-Agent": "TCGTools/1.17.1 (deck-import-dev)",
        "Accept": "text/html",
        "Cookie": "dk-language=2",
    },
)
with urllib.request.urlopen(req, timeout=30) as resp:
    body = resp.read()
path = Path("tests/unit/fixtures/ligamagic/deck_10187992_en.html")
path.write_bytes(body)
text = body.decode("utf-8", errors="replace")
names = re.findall(r"data-lc-name='([^']+)'", text)
print("bytes", len(body))
print("Path to Exile", "Path to Exile" in text)
print("Caminho", "Caminho" in text)
print("Snow-Covered", "Snow-Covered" in text)
print("sample names", names[:12])
print("lower price", re.search(r"class='price-head lower[^']*'>R\$\s*([^<]+)", text))
m = re.search(r"class='price-head lower[^']*'[^>]*>R\$\s*([^<]+)", text)
print("price match", m.group(1) if m else None)
