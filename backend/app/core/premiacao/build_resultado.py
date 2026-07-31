"""Build persisted premiação resultado."""

from __future__ import annotations

from typing import Any

from app.core.premiacao.calculator import calcular
from app.core.premiacao.se_payout import (
    BandPayout,
    PlayerPayout,
    SePayoutResult,
    assign_se_band_payouts,
    assign_swiss_payouts,
    preview_se_bands,
)
from app.core.premiacao.validation import validate_payout_conservation
from app.core.torneios.models import BandMember
from app.schemas.premiacao_resultado import validate_premiacao_resultado


def _band_to_dict(b: BandPayout) -> dict[str, Any]:
    return {
        "label": b.label,
        "pool": b.pool,
        "tier_indices": b.tier_indices,
        "player_count": b.player_count,
        "payout_per_player": b.payout_per_player,
    }


def _player_payout_to_dict(p: PlayerPayout) -> dict[str, Any]:
    return {
        "player_id": p.player_id,
        "name": p.name,
        "band_label": p.band_label,
        "payout": p.payout,
    }


def build_premiacao_resultado(
    *,
    format: str,
    n: int,
    config: dict[str, Any],
    third_place_match: bool,
    members: list[BandMember],
    standings_snapshot: list[dict[str, Any]],
    entry_fee: float,
) -> dict[str, Any]:
    if format == "single_elimination":
        payout = assign_se_band_payouts(n, config, members, third_place_match)
    else:
        ordered = [(m.player_id, m.name) for m in members if not m.is_drop]
        payout = assign_swiss_payouts(n, config, ordered)

    validate_payout_conservation(
        n,
        [p.payout for p in payout.player_payouts],
        config["casas_decimais"],
    )

    resultado = calcular(n, config)
    creditos: list[float] | None = None
    total_creditos: float | None = None
    if entry_fee > 0:
        creditos = [
            round(p.payout * entry_fee, config["casas_decimais"]) for p in payout.player_payouts
        ]
        total_creditos = round(n * entry_fee, config["casas_decimais"])

    base: dict[str, Any] = {
        "schema_version": 2 if format == "single_elimination" else 1,
        "jogadores": n,
        "premiados": resultado["premiados"],
        "premios": resultado["premios"],
        "entry_fee": entry_fee,
        "creditos": creditos,
        "total_creditos": total_creditos,
        "standings_snapshot": standings_snapshot,
    }

    if format == "single_elimination":
        base["bands"] = [_band_to_dict(b) for b in payout.bands]
        base["player_payouts"] = [_player_payout_to_dict(p) for p in payout.player_payouts]

    validated = validate_premiacao_resultado(base)
    return validated.to_dict()


def build_preview_calcular_response(
    n: int,
    config: dict[str, Any],
    formato: str,
    third_place_match: bool,
    valor_inscricao: float | None,
) -> dict[str, Any]:
    resultado = calcular(n, config)
    response: dict[str, Any] = {
        **resultado,
        "total_inscricoes": float(n),
        "creditos": None,
        "total_creditos": None,
        "bands": None,
    }
    if valor_inscricao is not None:
        response["creditos"] = [
            round(p * valor_inscricao, config["casas_decimais"]) for p in resultado["premios"]
        ]
        response["total_creditos"] = round(n * valor_inscricao, config["casas_decimais"])

    if formato == "single_elimination":
        bands = preview_se_bands(n, config, third_place_match)
        response["bands"] = [_band_to_dict(b) for b in bands]
        if valor_inscricao is not None:
            response["creditos"] = None
            band_creditos = []
            for b in bands:
                if b.payout_per_player is not None:
                    band_creditos.append(
                        round(b.payout_per_player * valor_inscricao, config["casas_decimais"])
                    )
            response["band_creditos"] = band_creditos

    return response
