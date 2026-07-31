"""Cálculo de premiados e distribuição proporcional de prêmios."""

from __future__ import annotations

from math import floor
from typing import Any


def calcular_premiados(jogadores: int, config: dict[str, Any]) -> int:
    """
    Define quantos colocados recebem prêmio.

    Fórmula:
        Y = min(max_premiados, max(min_premiados, floor((N + 1) / crescimento)))
    """
    min_premiados = config["min_premiados"]
    max_premiados = config["max_premiados"]
    crescimento = config["crescimento"]

    calculado = floor((jogadores + 1) / crescimento)
    premiados = min(max_premiados, max(min_premiados, calculado))
    return min(premiados, jogadores)


def calcular_pesos(quantidade: int, razao: float) -> list[float]:
    """Retorna pesos exponenciais: r^0, r^1, ..., r^(Y-1)."""
    return [razao ** indice for indice in range(quantidade)]


def _distribuir_residuo_maior_resto(
    valores_exatos: list[float],
    total: float,
    casas_decimais: int,
) -> list[float]:
    """
    Arredonda valores proporcionais pelo método do maior resto.

    O residual é distribuído entre as posições com maior parte fracionária,
    evitando concentrar todo o ajuste na última colocação.
    """
    fator = 10 ** casas_decimais
    total_unidades = round(total * fator)
    unidades = [floor(valor * fator + 1e-9) for valor in valores_exatos]

    residuo = total_unidades - sum(unidades)
    if residuo == 0:
        return [unidade / fator for unidade in unidades]

    ordenacao = sorted(
        range(len(unidades)),
        key=lambda indice: (
            valores_exatos[indice] * fator - unidades[indice],
            -indice,
        ),
        reverse=True,
    )

    for offset in range(residuo):
        indice = ordenacao[offset % len(ordenacao)]
        unidades[indice] += 1

    return [unidade / fator for unidade in unidades]


def split_pool(pool: float, count: int, casas_decimais: int) -> list[float]:
    """Split a band pool equally among ``count`` players with maior-resto rounding."""
    if count <= 0:
        return []
    valores_exatos = [pool / count] * count
    return _distribuir_residuo_maior_resto(valores_exatos, pool, casas_decimais)


def distribuir_premios(
    jogadores: int,
    premiados: int,
    config: dict[str, Any],
) -> list[float]:
    """Distribui ``jogadores`` inscrições entre ``premiados`` colocados."""
    razao = config["r"]
    casas_decimais = config["casas_decimais"]

    pesos = calcular_pesos(premiados, razao)
    soma_pesos = sum(pesos)
    valores_exatos = [jogadores * peso / soma_pesos for peso in pesos]

    return _distribuir_residuo_maior_resto(
        valores_exatos,
        float(jogadores),
        casas_decimais,
    )


def calcular(jogadores: int, config: dict[str, Any]) -> dict[str, Any]:
    """
    Calcula premiados e prêmios para um torneio.

    Returns:
        Dict com ``jogadores``, ``premiados`` e ``premios``.
        A soma de ``premios`` é sempre igual a ``jogadores``.
    """
    premiados = calcular_premiados(jogadores, config)
    premios = distribuir_premios(jogadores, premiados, config)

    return {
        "jogadores": jogadores,
        "premiados": premiados,
        "premios": premios,
    }
