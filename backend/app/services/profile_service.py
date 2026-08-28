"""Public player profile aggregation."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any

from sqlalchemy.orm import Session as DbSession, joinedload

from app.core.auth.avatars import user_avatar_url
from app.core.auth.fourse_points import ranking, user_fp_total
from app.core.auth.service import public_user_dict
from app.models import Event, FoursePointsLedger, Player, User, UserRole


MONTHS_PT = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]


def can_view_fp(viewer: User | None, subject: User) -> bool:
    if viewer is None:
        return False
    return viewer.id == subject.id or viewer.role == UserRole.admin.value


def _tcg_payload(ev: Event) -> dict[str, Any] | None:
    tcg = ev.tcg_game
    if tcg is None:
        return None
    return {
        "id": tcg.id,
        "name": tcg.name,
        "slug": tcg.slug,
        "color_hex": tcg.color_hex,
    }


def build_public_profile(
    db: DbSession,
    user: User,
    viewer: User | None,
) -> dict[str, Any]:
    show_fp = can_view_fp(viewer, user)
    is_owner = bool(viewer and viewer.id == user.id)

    players = db.query(Player).filter(Player.user_id == user.id).all()
    event_ids = [p.event_id for p in players]
    events: dict[int, Event] = {}
    if event_ids:
        rows = (
            db.query(Event)
            .options(joinedload(Event.tcg_game), joinedload(Event.players))
            .filter(Event.id.in_(event_ids))
            .all()
        )
        events = {e.id: e for e in rows}

    fp_by_event = {
        int(r.event_id): int(r.points or 0)
        for r in db.query(FoursePointsLedger)
        .filter(FoursePointsLedger.user_id == user.id)
        .all()
    }

    history: list[dict[str, Any]] = []
    for p in players:
        ev = events.get(p.event_id)
        if not ev or ev.status != "finished":
            continue
        snap = (ev.premiacao_resultado or {}).get("standings_snapshot") or []
        row = next((s for s in snap if s.get("player_id") == p.id), None)
        rank = row.get("rank") if row else None
        is_drop = row.get("is_drop") if row else bool(p.dropped_at)
        entry: dict[str, Any] = {
            "event_id": ev.id,
            "event_name": ev.name,
            "event_date": ev.event_date.isoformat(),
            "source": ev.source,
            "rank": rank,
            "rank_label": row.get("rank_label") if row else None,
            "is_drop": bool(is_drop),
            "decklist": p.decklist,
            "player_count": len(ev.players),
            "tcg_game": _tcg_payload(ev),
        }
        if show_fp:
            entry["fp_earned"] = fp_by_event.get(ev.id, 0)
        history.append(entry)
    history.sort(key=lambda h: h["event_date"], reverse=True)

    ranks = [h["rank"] for h in history if h["rank"] is not None and not h["is_drop"]]
    titles = sum(1 for r in ranks if r == 1)
    top8 = sum(1 for r in ranks if r <= 8)
    best = min(ranks) if ranks else None

    stats = {
        "tournaments": len(history),
        "titles": titles,
        "top8": top8,
        "best_finish": best,
    }

    fp_by_game: list[dict[str, Any]] = []
    fp_by_month: list[dict[str, Any]] = []
    if show_fp:
        fp_by_game_map: dict[str, dict[str, Any]] = {}
        for h in history:
            tcg = h.get("tcg_game")
            key = tcg["name"] if tcg else "Outros"
            bucket = fp_by_game_map.setdefault(
                key,
                {
                    "tcg_name": key,
                    "tcg_game": tcg,
                    "points": 0,
                    "tournaments": 0,
                },
            )
            bucket["points"] += int(h.get("fp_earned") or 0)
            bucket["tournaments"] += 1
        fp_by_game = sorted(fp_by_game_map.values(), key=lambda r: (-r["points"], r["tcg_name"]))

        month_points: dict[str, int] = defaultdict(int)
        month_counts: Counter[str] = Counter()
        for h in history:
            ym = h["event_date"][:7]
            month_points[ym] += int(h.get("fp_earned") or 0)
            month_counts[ym] += 1
        fp_by_month = [
            {"month": m, "points": month_points[m], "tournaments": month_counts[m]}
            for m in sorted(month_points.keys())
        ]
    else:
        month_counts = Counter(h["event_date"][:7] for h in history)

    insights = _build_insights(
        history,
        fp_by_game if show_fp else [],
        month_counts,
        best,
        second_person=is_owner,
    )

    rank_position = None
    total_fp = user_fp_total(db, user.id)
    if total_fp > 0:
        for row in ranking(db, limit=500):
            if row["user_id"] == user.id:
                rank_position = row["rank"]
                break

    payload: dict[str, Any] = {
        **public_user_dict(user),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "avatar_url": user_avatar_url(user.id, user.avatar_blob),
        "stats": stats,
        "insights": insights,
        "badge_games": [],
        "fp_by_game": fp_by_game if show_fp else [],
        "fp_by_month": fp_by_month if show_fp else [],
        "history": history,
        "ranking_position": rank_position if show_fp else None,
        "viewer_authenticated": viewer is not None,
        "can_edit": is_owner,
        "fourse_points_visible": show_fp,
        "fourse_points": total_fp if show_fp else None,
    }

    badge_games: list[dict[str, Any]] = []
    seen: set[int] = set()
    for h in history:
        tcg = h.get("tcg_game")
        if not tcg or tcg["id"] in seen:
            continue
        seen.add(tcg["id"])
        badge_games.append(tcg)
    payload["badge_games"] = badge_games
    return payload


def _build_insights(
    history: list[dict[str, Any]],
    fp_by_game: list[dict[str, Any]],
    month_counts: Counter[str],
    best: int | None,
    *,
    second_person: bool = False,
) -> list[str]:
    insights: list[str] = []
    if not history:
        return ["Ainda sem torneios finalizados neste perfil."]

    dates = [date.fromisoformat(h["event_date"]) for h in history]
    first, last = min(dates), max(dates)
    months_span = max(1, (last.year - first.year) * 12 + (last.month - first.month) + 1)
    avg = len(history) / months_span
    insights.append(f"Participa em média de {avg:.1f} torneios por mês.".replace(".", ","))

    if fp_by_game:
        best_game = max(fp_by_game, key=lambda g: (g["points"], g["tournaments"]))
        if second_person:
            insights.append(f"Seu melhor card game é {best_game['tcg_name']}.")
        else:
            insights.append(f"Melhor card game: {best_game['tcg_name']}.")

    if best is not None:
        if second_person:
            insights.append(f"Seu melhor resultado foi {best}º lugar.")
        else:
            insights.append(f"Melhor resultado: {best}º lugar.")

    if month_counts:
        top_month, _ = month_counts.most_common(1)[0]
        y, m = top_month.split("-")
        label = f"{MONTHS_PT[int(m) - 1].capitalize()} de {y}"
        if second_person:
            insights.append(f"Seu mês mais ativo foi {label}.")
        else:
            insights.append(f"Mês mais ativo: {label}.")

    return insights[:4]
