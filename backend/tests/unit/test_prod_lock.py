"""Validate production lockfile format."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

LOCK_PATH = Path(__file__).resolve().parents[2] / "requirements-prod.lock"
PIN_RE = re.compile(r"^[A-Za-z0-9_.-]+==[0-9]+(?:\.[0-9]+)*$")


def test_prod_lock_exists():
    assert LOCK_PATH.is_file()


def test_prod_lock_uses_exact_pins_only():
    lines = [
        ln.strip()
        for ln in LOCK_PATH.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    assert len(lines) >= 10
    bad = [ln for ln in lines if ">" in ln or "<" in ln or not PIN_RE.match(ln)]
    assert not bad, f"unpinned lines: {bad}"


def test_prod_lock_includes_core_packages():
    text = LOCK_PATH.read_text(encoding="utf-8").lower()
    for pkg in ("fastapi==", "uvicorn==", "sqlalchemy==", "alembic==", "pydantic=="):
        assert pkg in text
