"""SE band payout assignment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.premiacao.calculator import calcular, split_pool
from app.core.torneios.models import BandMember
from app.core.torneios.se_bands import BandDefinition, build_tier_bands


@dataclass
class PlayerPayout:
    player_id: int
    name: str
    band_label: str
    payout: float


@dataclass
class BandPayout:
    label: str
    pool: float
    tier_indices: list[int]
    player_count: int
    payout_per_player: float | None


@dataclass
class SePayoutResult:
    premios: list[float]
    bands: list[BandPayout]
    player_payouts: list[PlayerPayout]


def preview_se_bands(
    n: int,
    config: dict[str, Any],
    third_place_match: bool,
) -> list[BandPayout]:
    """Preview band pools without real player assignment."""
    resultado = calcular(n, config)
    premios = resultado["premios"]
    casas = config["casas_decimais"]
    band_defs = build_tier_bands(resultado["premiados"], third_place_match)
    bands: list[BandPayout] = []
    for band in band_defs:
        pool = sum(premios[i] for i in band.tier_indices if i < len(premios))
        per_player = None
        if band.nominal_size > 0:
            splits = split_pool(pool, band.nominal_size, casas)
            per_player = splits[0] if splits else None
        bands.append(
            BandPayout(
                label=band.label,
                pool=pool,
                tier_indices=list(band.tier_indices),
                player_count=band.nominal_size,
                payout_per_player=per_player,
            )
        )
    return bands


def assign_se_band_payouts(
    n: int,
    config: dict[str, Any],
    members: list[BandMember],
    third_place_match: bool,
) -> SePayoutResult:
    resultado = calcular(n, config)
    premios = resultado["premios"]
    casas = config["casas_decimais"]
    band_defs = build_tier_bands(resultado["premiados"], third_place_match)

    by_label: dict[str, list[BandMember]] = {}
    for m in members:
        if m.is_drop:
            continue
        by_label.setdefault(m.band_label, []).append(m)

    player_payouts: list[PlayerPayout] = []
    bands: list[BandPayout] = []
    undistributed = 0.0

    for band in band_defs:
        pool = sum(premios[i] for i in band.tier_indices if i < len(premios))
        eligible = by_label.get(band.label, [])
        count = len(eligible)
        per_player = None
        if count > 0:
            splits = split_pool(pool, count, casas)
            for member, payout in zip(eligible, splits):
                player_payouts.append(
                    PlayerPayout(
                        player_id=member.player_id,
                        name=member.name,
                        band_label=band.label,
                        payout=payout,
                    )
                )
            per_player = splits[0] if splits else None
        else:
            undistributed += pool
        bands.append(
            BandPayout(
                label=band.label,
                pool=pool,
                tier_indices=list(band.tier_indices),
                player_count=count,
                payout_per_player=per_player,
            )
        )

    if undistributed > 0 and player_payouts:
        extras = split_pool(undistributed, len(player_payouts), casas)
        player_payouts = [
            PlayerPayout(
                player_id=p.player_id,
                name=p.name,
                band_label=p.band_label,
                payout=round(p.payout + extra, casas),
            )
            for p, extra in zip(player_payouts, extras)
        ]

    return SePayoutResult(
        premios=premios,
        bands=bands,
        player_payouts=player_payouts,
    )


def assign_swiss_payouts(
    n: int,
    config: dict[str, Any],
    ordered_player_ids: list[tuple[int, str]],
) -> SePayoutResult:
    """One tier per active player in rank order."""
    resultado = calcular(n, config)
    premios = resultado["premios"]
    player_payouts: list[PlayerPayout] = []
    bands: list[BandPayout] = []
    for i, (pid, name) in enumerate(ordered_player_ids):
        if i >= len(premios):
            break
        payout = premios[i]
        label = f"{i + 1}º"
        player_payouts.append(
            PlayerPayout(player_id=pid, name=name, band_label=label, payout=payout)
        )
        bands.append(
            BandPayout(
                label=label,
                pool=payout,
                tier_indices=[i],
                player_count=1,
                payout_per_player=payout,
            )
        )
    return SePayoutResult(premios=premios, bands=bands, player_payouts=player_payouts)
