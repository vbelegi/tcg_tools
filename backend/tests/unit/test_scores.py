"""Score validation tests."""

import pytest

from app.core.torneios.scores import ScoreError, match_is_decided, validate_score


def test_bo3_win_1_0_time_limit():
    assert validate_score(1, 0, 3, allow_draw=False) == 1
    assert validate_score(0, 1, 3, allow_draw=False) == 2


def test_bo3_draw_0_0_swiss():
    assert validate_score(0, 0, 3, allow_draw=True) is None


def test_bo3_draw_swiss_nonzero():
    assert validate_score(1, 1, 3, allow_draw=True) is None


def test_se_no_draw():
    with pytest.raises(ScoreError):
        validate_score(0, 0, 3, allow_draw=False)


def test_unsubmitted_vs_submitted():
    assert not match_is_decided(0, 0, is_bye=False, is_walkover=False, scores_submitted=False, allow_draw=True)
    assert match_is_decided(0, 0, is_bye=False, is_walkover=False, scores_submitted=True, allow_draw=True)


def test_legacy_bo3_2_0_still_valid():
    assert validate_score(2, 0, 3, allow_draw=False) == 1


def test_bo3_rejects_3_0():
    with pytest.raises(ScoreError, match="máximo 2"):
        validate_score(3, 0, 3, allow_draw=False)


def test_bo1_only_0_and_1_per_player():
    assert validate_score(1, 0, 1, allow_draw=False) == 1
    with pytest.raises(ScoreError, match="máximo 1"):
        validate_score(2, 0, 1, allow_draw=False)


def test_bo5_allows_up_to_3():
    assert validate_score(3, 0, 5, allow_draw=False) == 1
    with pytest.raises(ScoreError, match="máximo 3"):
        validate_score(4, 0, 5, allow_draw=False)
