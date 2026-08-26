"""TCG games API."""

from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin
from app.db.session import get_db
from app.models import TcgGame

router = APIRouter(prefix="/tcg-games", tags=["tcg-games"])

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _slugify(name: str) -> str:
    raw = (name or "").strip().lower()
    out = []
    prev_dash = False
    for ch in raw:
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif ch in (" ", "-", "_") and not prev_dash:
            out.append("-")
            prev_dash = True
    slug = "".join(out).strip("-")
    return slug or "tcg"


def _game_dict(g: TcgGame) -> dict:
    return {
        "id": g.id,
        "name": g.name,
        "slug": g.slug,
        "color_hex": g.color_hex,
        "active": g.active,
    }


class TcgGameCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    color_hex: str
    slug: str | None = None
    active: bool = True

    @field_validator("color_hex")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        value = (v or "").strip()
        if not value.startswith("#"):
            value = f"#{value}"
        if not _HEX.match(value):
            raise ValueError("Cor deve ser hex #RRGGBB.")
        return value


class TcgGameUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    color_hex: str | None = None
    slug: str | None = None
    active: bool | None = None

    @field_validator("color_hex")
    @classmethod
    def validate_hex(cls, v: str | None) -> str | None:
        if v is None:
            return None
        value = v.strip()
        if not value.startswith("#"):
            value = f"#{value}"
        if not _HEX.match(value):
            raise ValueError("Cor deve ser hex #RRGGBB.")
        return value


@router.get("")
def list_tcg_games(
    db: Session = Depends(get_db),
    include_inactive: bool = False,
):
    q = db.query(TcgGame).order_by(TcgGame.name.asc())
    if not include_inactive:
        q = q.filter(TcgGame.active.is_(True))
    return [_game_dict(g) for g in q.all()]


@router.post("", status_code=201)
def create_tcg_game(body: TcgGameCreate, _: RequireAdmin, db: Session = Depends(get_db)):
    name = body.name.strip()
    slug = (body.slug or _slugify(name)).strip().lower()
    if not _SLUG.match(slug):
        raise HTTPException(status_code=400, detail="Slug inválido.")
    if db.query(TcgGame).filter((TcgGame.name == name) | (TcgGame.slug == slug)).first():
        raise HTTPException(status_code=400, detail="TCG já cadastrado.")
    row = TcgGame(
        name=name,
        slug=slug,
        color_hex=body.color_hex,
        active=body.active,
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _game_dict(row)


@router.patch("/{game_id}")
def update_tcg_game(
    game_id: int,
    body: TcgGameUpdate,
    _: RequireAdmin,
    db: Session = Depends(get_db),
):
    row = db.query(TcgGame).filter(TcgGame.id == game_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="TCG não encontrado.")
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        name = data["name"].strip()
        dup = db.query(TcgGame).filter(TcgGame.name == name, TcgGame.id != game_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="Nome já em uso.")
        row.name = name
    if "slug" in data and data["slug"] is not None:
        slug = data["slug"].strip().lower()
        if not _SLUG.match(slug):
            raise HTTPException(status_code=400, detail="Slug inválido.")
        dup = db.query(TcgGame).filter(TcgGame.slug == slug, TcgGame.id != game_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="Slug já em uso.")
        row.slug = slug
    if "color_hex" in data and data["color_hex"] is not None:
        row.color_hex = data["color_hex"]
    if "active" in data and data["active"] is not None:
        row.active = bool(data["active"])
    db.commit()
    db.refresh(row)
    return _game_dict(row)


@router.delete("/{game_id}", status_code=204)
def delete_tcg_game(game_id: int, _: RequireAdmin, db: Session = Depends(get_db)):
    row = db.query(TcgGame).filter(TcgGame.id == game_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="TCG não encontrado.")
    # Soft-delete preferred to keep history on events
    row.active = False
    db.commit()
    return None
