"""Fourse Points (FP) calculation and ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.core.auth.avatars import media_url
from app.core.premiacao.calculator import calcular_premiados, distribuir_premios
from app.models import FoursePointsLedger, User

DEFAULT_FP_K = 10


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def fp_k_from_preset(preset: dict[str, Any] | None) -> int:
    if not preset:
        return DEFAULT_FP_K
    raw = preset.get("fp_k", DEFAULT_FP_K)
    try:
        k = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_FP_K
    return k if k > 0 else DEFAULT_FP_K


def compute_fp_awards(
    *,
    n: int,
    config: dict[str, Any],
    placements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    placements: [{user_id, placement, is_drop?}]
    placement is 1-based rank among non-drop finishers for premio index.
    Drop/WO → 0 FP.
    """
    if n <= 0:
        return []
    k = fp_k_from_preset(config)
    cfg = {key: val for key, val in config.items() if key not in ("label", "fp_k")}
    y = calcular_premiados(n, cfg)
    fractions = distribuir_premios(n, y, cfg)  # sum == n
    awards: list[dict[str, Any]] = []
    for row in placements:
        user_id = row.get("user_id")
        if not user_id:
            continue
        is_drop = bool(row.get("is_drop"))
        placement = row.get("placement")
        if is_drop or placement is None:
            points = 0
            reason = "drop_or_wo"
        else:
            idx = int(placement) - 1
            if 0 <= idx < len(fractions):
                points = int(round(fractions[idx] * k))
                reason = "placement"
            else:
                points = 0
                reason = "unpaid_placement"
        awards.append(
            {
                "user_id": int(user_id),
                "placement": None if is_drop else placement,
                "points": points,
                "reason": reason,
            }
        )
    return awards


def replace_event_fp_ledger(
    db: DbSession,
    event_id: int,
    awards: list[dict[str, Any]],
) -> None:
    db.query(FoursePointsLedger).filter(FoursePointsLedger.event_id == event_id).delete()
    now = _now()
    for award in awards:
        db.add(
            FoursePointsLedger(
                user_id=award["user_id"],
                event_id=event_id,
                placement=award.get("placement"),
                points=int(award["points"]),
                reason=award["reason"],
                created_at=now,
            )
        )
    db.commit()


def ranking(db: DbSession, *, limit: int = 100) -> list[dict[str, Any]]:
    rows = (
        db.query(User.id, User.display_name, User.avatar_path, FoursePointsLedger.points)
        .join(FoursePointsLedger, FoursePointsLedger.user_id == User.id)
        .all()
    )
    totals: dict[int, dict[str, Any]] = {}
    for uid, name, avatar_path, pts in rows:
        bucket = totals.setdefault(
            uid,
            {
                "user_id": uid,
                "display_name": name,
                "avatar_url": media_url(avatar_path),
                "points": 0,
            },
        )
        bucket["points"] += int(pts or 0)
        if bucket.get("avatar_url") is None:
            bucket["avatar_url"] = media_url(avatar_path)
    ordered = sorted(totals.values(), key=lambda r: (-r["points"], r["display_name"].lower()))
    ordered = [row for row in ordered if int(row.get("points") or 0) > 0]
    for i, row in enumerate(ordered[:limit], start=1):
        row["rank"] = i
    return ordered[:limit]


def user_fp_total(db: DbSession, user_id: int) -> int:
    rows = db.query(FoursePointsLedger.points).filter(FoursePointsLedger.user_id == user_id).all()
    return sum(int(r[0] or 0) for r in rows)
