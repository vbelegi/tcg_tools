"""Deck import API (LigaMagic preview)."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.deck_import import DeckImportError, import_ligamagic_preview
from app.core.rate_limit import check_rate_limit_scope, client_ip
from app.models import User

router = APIRouter(prefix="/decks", tags=["decks"])


class DeckImportPreviewBody(BaseModel):
    url: str = Field(min_length=8, max_length=500)


class DeckImportPreviewResponse(BaseModel):
    source: str
    source_deck_id: str
    source_url: str
    name: str | None
    format: str | None
    plain_text: str
    card_count: int
    price_low_brl: Decimal | None
    price_currency: str
    warnings: list[str]


@router.post("/import/preview", response_model=DeckImportPreviewResponse)
def preview_deck_import(
    body: DeckImportPreviewBody,
    request: Request,
    user: User = Depends(get_current_user),
):
    check_rate_limit_scope("deck_import_preview_ip", client_ip(request), limit=20, window_sec=3600)
    check_rate_limit_scope("deck_import_preview_user", str(user.id), limit=30, window_sec=3600)
    try:
        snap = import_ligamagic_preview(body.url)
    except DeckImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DeckImportPreviewResponse(
        source=snap.source,
        source_deck_id=snap.source_deck_id,
        source_url=snap.source_url,
        name=snap.name,
        format=snap.format,
        plain_text=snap.plain_text,
        card_count=snap.card_count,
        price_low_brl=snap.price_low_brl,
        price_currency=snap.price_currency,
        warnings=snap.warnings,
    )
