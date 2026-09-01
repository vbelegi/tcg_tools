"""Helpers for SQL LIKE / ILIKE user input."""


def escape_like(term: str) -> str:
    """Escape %, _ and backslash for use with escape='\\\\'."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def ilike_contains(term: str) -> str:
    cleaned = (term or "").strip()
    if not cleaned:
        return "%"
    return f"%{escape_like(cleaned)}%"
