"""Exportação de tabelas de premiação."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from core.paths import EXPORTS_DIR


def nome_arquivo_csv(min_jogadores: int, limite: int) -> str:
    return f"premiacao_{min_jogadores}_a_{limite}.csv"


def caminho_csv(min_jogadores: int, limite: int) -> Path:
    return EXPORTS_DIR / nome_arquivo_csv(min_jogadores, limite)


def listar_exports() -> list[Path]:
    """Lista arquivos CSV de premiação em ``exports/``."""
    if not EXPORTS_DIR.exists():
        return []
    return sorted(EXPORTS_DIR.glob("premiacao_*.csv"))


def limpar_exports() -> int:
    """
    Remove todos os exports de premiação.

    Returns:
        Quantidade de arquivos removidos.
    """
    arquivos = listar_exports()
    for arquivo in arquivos:
        arquivo.unlink()
    return len(arquivos)


def salvar_csv(
    resultados: list[dict[str, Any]],
    min_jogadores: int,
    limite: int,
) -> tuple[str, bool]:
    """
    Salva tabela de premiação em CSV.

    Se o arquivo já existir, ele é substituído.

    Returns:
        Tupla ``(caminho_absoluto, substituiu_existente)``.
    """
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    arquivo = caminho_csv(min_jogadores, limite)
    substituiu = arquivo.exists()

    max_premiados = max(resultado["premiados"] for resultado in resultados)

    with arquivo.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")

        cabecalho = ["Jogadores", "Premiados"]
        cabecalho.extend(f"{posicao}º Lugar" for posicao in range(1, max_premiados + 1))
        writer.writerow(cabecalho)

        for resultado in resultados:
            linha = [resultado["jogadores"], resultado["premiados"]]
            linha.extend(resultado["premios"])

            while len(linha) < max_premiados + 2:
                linha.append("")

            writer.writerow(linha)

    return str(arquivo.resolve()), substituiu
