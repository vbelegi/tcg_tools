"""Simple in-memory rate limiting (per client IP + endpoint key)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import HTTPException, Request

_LOCK = threading.Lock()
_HITS: dict[tuple[str, str], list[float]] = defaultdict(list)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _prune(hits: list[float], now: float, window_sec: int) -> list[float]:
    cutoff = now - window_sec
    return [t for t in hits if t > cutoff]


def _check_bucket(bucket: tuple[str, str], *, limit: int, window_sec: int) -> None:
    now = time.monotonic()
    with _LOCK:
        hits = _prune(_HITS[bucket], now, window_sec)
        if len(hits) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Muitas tentativas. Aguarde um momento e tente novamente.",
            )
        hits.append(now)
        _HITS[bucket] = hits


def check_rate_limit(key: str, ip: str, *, limit: int, window_sec: int) -> None:
    _check_bucket((ip, key), limit=limit, window_sec=window_sec)


def check_rate_limit_scope(scope: str, identifier: str, *, limit: int, window_sec: int) -> None:
    """Rate limit by arbitrary scope (e.g. user id or normalized email)."""
    _check_bucket((scope, identifier), limit=limit, window_sec=window_sec)


def rate_limit_dependency(
    key: str,
    *,
    limit: int = 10,
    window_sec: int = 60,
) -> Callable[..., None]:
    def _dep(request: Request) -> None:
        check_rate_limit(key, client_ip(request), limit=limit, window_sec=window_sec)

    return _dep


def reset_rate_limits_for_tests() -> None:
    with _LOCK:
        _HITS.clear()
