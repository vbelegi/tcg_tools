"""Promotional actions API.

Fase A wires the router only; CRUD, regulation upload, enrollment and draw
endpoints land in the following phases.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["acoes"])
