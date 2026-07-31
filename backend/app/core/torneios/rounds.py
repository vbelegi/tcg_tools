"""Round count calculation."""

from __future__ import annotations

import math


def calcular_rodadas(n: int) -> int:
    """R = ceil(log2(N))"""
    if n < 2:
        return 1
    return math.ceil(math.log2(n))
