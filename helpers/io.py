"""Utilitários de entrada do usuário."""

from __future__ import annotations

from core.validation import InputError


def ler_inteiro(
    prompt: str,
    *,
    minimo: int | None = None,
    maximo: int | None = None,
) -> int:
    """Lê um inteiro validado do terminal."""
    texto = input(prompt).strip()

    try:
        valor = int(texto)
    except ValueError as exc:
        raise InputError("Informe um número inteiro válido.") from exc

    if minimo is not None and valor < minimo:
        raise InputError(f"O valor mínimo permitido é {minimo}.")

    if maximo is not None and valor > maximo:
        raise InputError(f"O valor máximo permitido é {maximo}.")

    return valor


def ler_float_opcional(prompt: str) -> float | None:
    """Lê um float opcional; ENTER retorna None."""
    texto = input(prompt).strip()
    if not texto:
        return None

    try:
        return float(texto.replace(",", "."))
    except ValueError as exc:
        raise InputError("Informe um valor numérico válido.") from exc


def confirmar(prompt: str) -> bool:
    """Retorna True quando o usuário confirma com S/s."""
    resposta = input(prompt).strip().lower()
    return resposta in {"s", "sim"}
