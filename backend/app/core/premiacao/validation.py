"""Validação de configuração e entradas de torneio."""

from __future__ import annotations

REQUIRED_CONFIG_KEYS = (
    "min_jogadores",
    "min_premiados",
    "max_premiados",
    "crescimento",
    "r",
    "casas_decimais",
)

INT_CONFIG_KEYS = (
    "min_jogadores",
    "min_premiados",
    "max_premiados",
    "crescimento",
    "casas_decimais",
)

FLOAT_CONFIG_KEYS = ("r",)


class ConfigError(ValueError):
    """Erro de validação do arquivo de configuração."""


class InputError(ValueError):
    """Erro de validação de entrada do usuário."""


class PayoutConservationError(ValueError):
    """Soma dos payouts difere do número de inscrições."""


def validate_payout_conservation(
    n_players: int,
    payouts: list[float] | dict[int, float],
    casas_decimais: int,
) -> None:
    """Raises PayoutConservationError if sum of payouts != n_players."""
    if isinstance(payouts, dict):
        total = sum(payouts.values())
    else:
        total = sum(payouts)
    tolerance = 10 ** (-casas_decimais) if casas_decimais > 0 else 1e-9
    if abs(total - n_players) > tolerance:
        raise PayoutConservationError(
            f"Soma dos prêmios ({total}) difere de N inscrições ({n_players})."
        )


def validar_config(config: dict) -> None:
    """Valida estrutura e valores de preset de premiação."""
    if not isinstance(config, dict):
        raise ConfigError("Configuração deve ser um objeto JSON.")

    for chave in REQUIRED_CONFIG_KEYS:
        if chave not in config:
            raise ConfigError(f"Campo obrigatório ausente: {chave}.")

    extras = set(config) - set(REQUIRED_CONFIG_KEYS) - {"label", "fp_k"}
    if extras:
        raise ConfigError(f"Campos desconhecidos: {', '.join(sorted(extras))}.")

    for chave in INT_CONFIG_KEYS:
        valor = config[chave]
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ConfigError(f"{chave} deve ser um número inteiro.")
        if valor < 0:
            raise ConfigError(f"{chave} não pode ser negativo.")

    if "fp_k" in config and config["fp_k"] is not None:
        fp_k = config["fp_k"]
        if isinstance(fp_k, bool) or not isinstance(fp_k, int) or fp_k < 1:
            raise ConfigError("fp_k deve ser um inteiro >= 1.")

    for chave in FLOAT_CONFIG_KEYS:
        valor = config[chave]
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ConfigError(f"{chave} deve ser um número.")
        config[chave] = float(valor)

    min_jogadores = config["min_jogadores"]
    min_premiados = config["min_premiados"]
    max_premiados = config["max_premiados"]
    crescimento = config["crescimento"]
    r = config["r"]
    casas = config["casas_decimais"]

    if min_jogadores < 1:
        raise ConfigError("min_jogadores deve ser pelo menos 1.")

    if min_premiados < 1:
        raise ConfigError("min_premiados deve ser pelo menos 1.")

    if max_premiados < min_premiados:
        raise ConfigError("max_premiados deve ser >= min_premiados.")

    if crescimento < 1:
        raise ConfigError("crescimento deve ser pelo menos 1.")

    if not 0 < r < 1:
        raise ConfigError("r deve estar entre 0 e 1 (exclusive).")

    if casas > 4:
        raise ConfigError("casas_decimais não pode ser maior que 4.")


def validar_jogadores(jogadores: int, config: dict) -> None:
    """Valida quantidade de jogadores para um torneio."""
    min_jogadores = config["min_jogadores"]

    if jogadores < min_jogadores:
        raise InputError(
            f"Quantidade mínima de jogadores: {min_jogadores}."
        )

    if jogadores < config["min_premiados"]:
        raise InputError(
            "Número de jogadores menor que o mínimo de premiados "
            f"({config['min_premiados']})."
        )


def validar_limite_tabela(limite: int, config: dict) -> None:
    """Valida limite superior ao gerar tabela de premiação."""
    min_jogadores = config["min_jogadores"]

    if limite < min_jogadores:
        raise InputError(
            f"O limite deve ser pelo menos {min_jogadores} jogadores."
        )


def validar_valor_inscricao(valor: float) -> None:
    """Valida valor monetário da inscrição."""
    if valor <= 0:
        raise InputError("Valor da inscrição deve ser maior que zero.")
