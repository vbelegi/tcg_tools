"""FastAPI dependency stubs for future auth."""

from __future__ import annotations

from typing import Any


def get_current_user() -> None:
    """Stub: auth não implementada na v1."""
    return None


def get_optional_user() -> dict[str, Any] | None:
    return None
