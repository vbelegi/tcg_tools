"""SE band definitions shared by standings and premiação.

Maps absolute tier indices from the premiação preset into placement bands
(1º, 2º, 3–4 or 3º/4º with bronze, 5–8, …). Spec: ``docs/modelo_premiacao.md``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BandDefinition:
    label: str
    tier_indices: tuple[int, ...]
    nominal_size: int


def format_band_label(lo: int, hi: int) -> str:
    if lo == hi:
        return f"{lo}º"
    return f"{lo}–{hi}"


def build_tier_bands(premiados: int, third_place_match: bool) -> list[BandDefinition]:
    """Group absolute tier indices into SE placement bands."""
    if premiados < 1:
        return []

    bands: list[BandDefinition] = []
    bands.append(BandDefinition(label="1º", tier_indices=(0,), nominal_size=1))
    if premiados < 2:
        return bands

    bands.append(BandDefinition(label="2º", tier_indices=(1,), nominal_size=1))
    if premiados < 3:
        return bands

    if third_place_match:
        if premiados >= 3:
            bands.append(BandDefinition(label="3º", tier_indices=(2,), nominal_size=1))
        if premiados >= 4:
            bands.append(BandDefinition(label="4º", tier_indices=(3,), nominal_size=1))
        next_index = 4
    else:
        if premiados >= 3:
            indices = tuple(range(2, min(4, premiados)))
            bands.append(
                BandDefinition(
                    label=format_band_label(3, 4),
                    tier_indices=indices,
                    nominal_size=2,
                )
            )
        next_index = 4

    block_power = 2
    while next_index < premiados:
        block_size = min(2**block_power, premiados - next_index)
        indices = tuple(range(next_index, next_index + block_size))
        lo = next_index + 1
        hi = next_index + block_size
        bands.append(
            BandDefinition(
                label=format_band_label(lo, hi),
                tier_indices=indices,
                nominal_size=block_size,
            )
        )
        next_index += block_size
        block_power += 1

    return bands
