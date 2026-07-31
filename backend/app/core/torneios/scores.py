"""Score validation."""

from __future__ import annotations


class ScoreError(ValueError):
    pass


def wins_to_win(best_of: int) -> int:
    return (best_of + 1) // 2


def validate_score(
    score_p1: int,
    score_p2: int,
    best_of: int,
    *,
    allow_draw: bool,
) -> int | None:
    """
    Validate match score. Returns winner side: 1, 2, or None for draw.

    Time-limited matches may end 1-0 in Bo3/Bo5 (winner = higher score, min 1 game).
    0-0 is a valid intentional draw (Swiss), distinct from an unsubmitted result.
    """
    if score_p1 < 0 or score_p2 < 0:
        raise ScoreError("Placar não pode ser negativo.")
    max_games = wins_to_win(best_of)
    if score_p1 > max_games or score_p2 > max_games:
        raise ScoreError(
            f"Cada jogador pode ter no máximo {max_games} game(s) vencido(s) no melhor de {best_of}."
        )
    total = score_p1 + score_p2
    if total > best_of:
        raise ScoreError(f"Soma de games excede melhor de {best_of}.")

    if score_p1 == score_p2:
        if not allow_draw:
            raise ScoreError("Eliminatória não permite empate.")
        return None

    if score_p1 < 1 and score_p2 < 1:
        raise ScoreError("Informe o placar.")

    if score_p1 > score_p2:
        return 1
    return 2


def match_is_decided(
    score_p1: int,
    score_p2: int,
    *,
    is_bye: bool,
    is_walkover: bool,
    scores_submitted: bool,
    allow_draw: bool,
    best_of: int = 5,
) -> bool:
    if is_bye or is_walkover:
        return True
    if not scores_submitted:
        return False
    try:
        validate_score(score_p1, score_p2, best_of, allow_draw=allow_draw)
        return True
    except ScoreError:
        return False
