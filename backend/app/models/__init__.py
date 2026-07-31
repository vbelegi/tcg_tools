"""SQLAlchemy ORM models."""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventFormat(str, enum.Enum):
    swiss = "swiss"
    single_elimination = "single_elimination"


class EventStatus(str, enum.Enum):
    draft = "draft"
    running = "running"
    finished = "finished"


class RoundStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    completed = "completed"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    max_rounds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    entry_fee: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    best_of: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    premiacao_preset: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    premiacao_resultado: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=EventStatus.draft.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shuffle_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    third_place_match: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    se_bo_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    players: Mapped[list[Player]] = relationship(back_populates="event", cascade="all, delete-orphan")
    rounds: Mapped[list[Round]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (Index("ix_players_event_id", "event_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dropped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    registration_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    decklist: Mapped[str | None] = mapped_column(Text, nullable=True)

    event: Mapped[Event] = relationship(back_populates="players")


class Round(Base):
    __tablename__ = "rounds"
    __table_args__ = (Index("ix_rounds_event_id", "event_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=RoundStatus.pending.value)

    event: Mapped[Event] = relationship(back_populates="rounds")
    matches: Mapped[list[Match]] = relationship(back_populates="round", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_matches_round_id", "round_id"),
        Index("ix_matches_player1_id", "player1_id"),
        Index("ix_matches_player2_id", "player2_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id"), nullable=False)
    player1_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    player2_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    score_p1: Mapped[int] = mapped_column(Integer, default=0)
    score_p2: Mapped[int] = mapped_column(Integer, default=0)
    is_bye: Mapped[bool] = mapped_column(Boolean, default=False)
    is_walkover: Mapped[bool] = mapped_column(Boolean, default=False)
    had_rematch: Mapped[bool] = mapped_column(Boolean, default=False)
    scores_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_third_place: Mapped[bool] = mapped_column(Boolean, default=False)
    best_of: Mapped[int | None] = mapped_column(Integer, nullable=True)

    round: Mapped[Round] = relationship(back_populates="matches")
