"""Fourse Points unit tests."""

from __future__ import annotations

from app.core.auth.fourse_points import DEFAULT_FP_K, compute_fp_awards


def test_fp_scales_with_n():
    config = {
        "min_jogadores": 4,
        "min_premiados": 2,
        "max_premiados": 8,
        "crescimento": 4,
        "r": 0.5,
        "casas_decimais": 2,
        "fp_k": 10,
    }
    small = compute_fp_awards(
        n=4,
        config=config,
        placements=[{"user_id": 1, "placement": 1, "is_drop": False}],
    )
    large = compute_fp_awards(
        n=32,
        config=config,
        placements=[{"user_id": 1, "placement": 1, "is_drop": False}],
    )
    assert small[0]["points"] < large[0]["points"]
    assert small[0]["points"] > 0


def test_fp_drop_is_zero():
    config = {
        "min_jogadores": 4,
        "min_premiados": 2,
        "max_premiados": 8,
        "crescimento": 4,
        "r": 0.5,
        "casas_decimais": 2,
        "fp_k": DEFAULT_FP_K,
    }
    awards = compute_fp_awards(
        n=8,
        config=config,
        placements=[
            {"user_id": 1, "placement": 1, "is_drop": False},
            {"user_id": 2, "placement": None, "is_drop": True},
        ],
    )
    by_user = {a["user_id"]: a["points"] for a in awards}
    assert by_user[1] > 0
    assert by_user[2] == 0
