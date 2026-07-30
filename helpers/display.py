"""Formatação e exibição de resultados."""

from __future__ import annotations

from typing import Any

TERMO_CREDITOS = "Créditos na Loja"


def formatar_moeda(valor: float, casas: int = 2) -> str:
    return f"R$ {valor:.{casas}f}"


def exibir_resultado_torneio(
    resultado: dict[str, Any],
    config: dict[str, Any],
    valor_inscricao: float | None = None,
) -> None:
    """Exibe prêmios em inscrições e, opcionalmente, em Créditos na Loja."""
    casas = config["casas_decimais"]
    jogadores = resultado["jogadores"]
    premios = resultado["premios"]
    total_inscricoes = sum(premios)

    print("\n======================================")
    print("Resultado")
    print("======================================")
    print(f"Jogadores : {jogadores}")
    print(f"Premiados : Top {resultado['premiados']}")
    print(f"Total     : {total_inscricoes:.{casas}f} inscrições")
    print()

    if valor_inscricao is not None:
        arrecadacao = jogadores * valor_inscricao
        print(f"Arrecadação total : {formatar_moeda(arrecadacao)}")
        print(f"Pagamento em {TERMO_CREDITOS} (centavos permitidos).")
        print()

        for posicao, premio in enumerate(premios, start=1):
            creditos = premio * valor_inscricao
            print(f"{posicao}º Lugar")
            print(f"   {premio:.{casas}f} inscrições")
            print(f"   {formatar_moeda(creditos, casas)} em {TERMO_CREDITOS}")
            print()
    else:
        for posicao, premio in enumerate(premios, start=1):
            print(f"{posicao}º Lugar -> {premio:.{casas}f} inscrições")


def exibir_linha_tabela(resultado: dict[str, Any], config: dict[str, Any]) -> None:
    """Exibe uma linha resumida da tabela de premiação."""
    casas = config["casas_decimais"]

    print(
        f"{resultado['jogadores']:>2} jogadores | "
        f"Top {resultado['premiados']} | ",
        end="",
    )

    for premio in resultado["premios"]:
        print(f"{premio:.{casas}f}", end=" | ")

    print()
