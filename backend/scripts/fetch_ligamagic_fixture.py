"""Download LigaMagic EN deck HTML for parser fixtures (dev only)."""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

URL = "https://www.ligamagic.com.br/?view=dks/deck&id=10187992"
OUT = Path(__file__).resolve().parents[1] / "tests" / "unit" / "fixtures" / "ligamagic" / "deck_10187992_en.html"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "TCGTools/1.16.1 (deck-import-dev)",
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    OUT.write_bytes(data)
    text = data.decode("utf-8", errors="replace")
    print("wrote", OUT, "bytes", len(data))
    for needle in ("Momo", "Snow-Covered", "Commander", "Maybeboard", "export"):
        print(f"  count[{needle}]={text.count(needle)}")
    for m in re.finditer(r"R\$\s*[\d.,]+", text):
        ctx = text[max(0, m.start() - 100) : m.start() + 30].replace("\n", " ")
        print("price:", ctx[:160])
        if m.start() > 50000:
            break


if __name__ == "__main__":
    main()
