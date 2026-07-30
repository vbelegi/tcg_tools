"""Ponto de entrada da calculadora de premiação TCG."""

from __future__ import annotations

from core.calculator import calcular
from core.config import load, save
from core.validation import (
    ConfigError,
    InputError,
    validar_config,
    validar_jogadores,
    validar_limite_tabela,
    validar_valor_inscricao,
)
from helpers.display import exibir_linha_tabela, exibir_resultado_torneio
from helpers.export import limpar_exports, listar_exports, salvar_csv
from helpers.io import confirmar, ler_float_opcional, ler_inteiro


def mostrar_menu() -> None:
    print("\n======================================")
    print("      Calculadora de Premiação TCG")
    print("======================================")
    print("1 - Calcular um torneio")
    print("2 - Gerar tabela até N jogadores")
    print("3 - Configurações")
    print("0 - Sair")


def _perguntar_limpar_exports() -> None:
    exports = listar_exports()
    if not exports:
        return

    print(f"\nExistem {len(exports)} export(s) em exports/.")
    if confirmar("Deseja limpar exports anteriores? (S/N): "):
        removidos = limpar_exports()
        print(f"\n{removidos} arquivo(s) removido(s) de exports/.")


def _menu_limpar_exports() -> None:
    exports = listar_exports()

    if not exports:
        print("\nNenhum export encontrado em exports/.")
        return

    print(f"\nExports encontrados ({len(exports)}):")
    for arquivo in exports:
        print(f"  - {arquivo.name}")

    if confirmar("\nDeseja remover todos? (S/N): "):
        removidos = limpar_exports()
        print(f"\n{removidos} arquivo(s) removido(s) de exports/.")


def calcular_torneio(cfg: dict) -> None:
    try:
        jogadores = ler_inteiro("\nQuantidade de jogadores: ")
        validar_jogadores(jogadores, cfg)
        resultado = calcular(jogadores, cfg)

        valor = ler_float_opcional(
            "Valor da inscrição (ENTER para ignorar): "
        )
        if valor is not None:
            validar_valor_inscricao(valor)

        exibir_resultado_torneio(resultado, cfg, valor)
    except (InputError, ConfigError) as exc:
        print(f"\nErro: {exc}")


def gerar_tabela(cfg: dict) -> None:
    try:
        limite = ler_inteiro("\nGerar tabela até quantos jogadores? ")
        validar_limite_tabela(limite, cfg)

        min_jogadores = cfg["min_jogadores"]
        resultados = []

        print()

        for jogadores in range(min_jogadores, limite + 1):
            resultado = calcular(jogadores, cfg)
            resultados.append(resultado)
            exibir_linha_tabela(resultado, cfg)

        if not resultados:
            print("\nNenhum resultado gerado.")
            return

        if confirmar("\nSalvar CSV? (S/N): "):
            caminho, substituiu = salvar_csv(resultados, min_jogadores, limite)
            print(f"\nCSV salvo em:\n{caminho}")
            if substituiu:
                print("(Arquivo existente substituído.)")
    except (InputError, ConfigError) as exc:
        print(f"\nErro: {exc}")


def configuracoes(cfg: dict) -> None:
    campos_editaveis = (
        "min_jogadores",
        "min_premiados",
        "max_premiados",
        "crescimento",
        "r",
        "casas_decimais",
    )

    while True:
        print("\n============================")
        print("Configurações")
        print("============================")

        for chave, valor in cfg.items():
            print(f"{chave}: {valor}")

        print()

        campo = input(
            "Campo para alterar\n"
            "(min_jogadores, min_premiados, max_premiados,\n"
            " crescimento, r, casas_decimais,\n"
            " limpar_exports)\n"
            "ENTER para voltar\n> ",
        ).strip()

        if campo == "":
            return

        if campo == "limpar_exports":
            _menu_limpar_exports()
            continue

        if campo not in campos_editaveis:
            print("\nCampo inválido.")
            continue

        valor_texto = input("Novo valor: ").strip()

        try:
            novo_cfg = cfg.copy()

            if "." in valor_texto or campo == "r":
                novo_cfg[campo] = float(valor_texto.replace(",", "."))
            else:
                novo_cfg[campo] = int(valor_texto)

            validar_config(novo_cfg)

            if save(novo_cfg):
                cfg.clear()
                cfg.update(novo_cfg)
                print("\nConfiguração salva.")
                _perguntar_limpar_exports()
            else:
                print("\nNenhuma alteração detectada.")

        except (ValueError, ConfigError) as exc:
            print(f"\nValor inválido: {exc}")


def main() -> None:
    cfg = load()

    while True:
        mostrar_menu()
        opcao = input("\nEscolha: ").strip()

        if opcao == "0":
            break
        if opcao == "1":
            calcular_torneio(cfg)
        elif opcao == "2":
            gerar_tabela(cfg)
        elif opcao == "3":
            configuracoes(cfg)
        else:
            print("\nOpção inválida.")


if __name__ == "__main__":
    main()
