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
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
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


class EventSource(str, enum.Enum):
    internal = "internal"
    external = "external"


class PairingMode(str, enum.Enum):
    platform = "platform"
    manual = "manual"


class RoundStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    completed = "completed"


class UserRole(str, enum.Enum):
    admin = "admin"
    staff = "staff"
    player = "player"


class UserStatus(str, enum.Enum):
    incomplete = "incomplete"
    active = "active"
    deleted = "deleted"


class Attendance(str, enum.Enum):
    pending = "pending"
    checked_in = "checked_in"


class RegistrationSource(str, enum.Enum):
    staff = "staff"
    self = "self"


class PromoActionType(str, enum.Enum):
    raffle_purchase_right = "raffle_purchase_right"


class PromoParticipantStatus(str, enum.Enum):
    pending_verification = "pending_verification"
    confirmed = "confirmed"


class PromoDrawMode(str, enum.Enum):
    direct = "direct"
    chained = "chained"


class TcgGame(Base):
    __tablename__ = "tcg_games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    events: Mapped[list[Event]] = relationship(back_populates="tcg_game")


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
    source: Mapped[str] = mapped_column(String(16), nullable=False, default=EventSource.internal.value)
    pairing_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PairingMode.platform.value
    )
    registration_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fp_n_at_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    external_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    tcg_game_id: Mapped[int | None] = mapped_column(
        ForeignKey("tcg_games.id", ondelete="SET NULL"), nullable=True
    )

    tcg_game: Mapped[TcgGame | None] = relationship(back_populates="events")
    players: Mapped[list[Player]] = relationship(back_populates="event", cascade="all, delete-orphan")
    rounds: Mapped[list[Round]] = relationship(back_populates="event", cascade="all, delete-orphan")
    fp_entries: Mapped[list[FoursePointsLedger]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


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
    attendance: Mapped[str] = mapped_column(String(16), nullable=False, default=Attendance.checked_in.value)
    registration_source: Mapped[str] = mapped_column(
        String(16), nullable=False, default=RegistrationSource.staff.value
    )

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


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("phone", name="uq_users_phone"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    guardian_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    guardian_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    guardian_relation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default=UserRole.player.value)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=UserStatus.incomplete.value)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    privacy_accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    privacy_policy_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    terms_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    marketing_opt_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    marketing_opt_out_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    marketing_opt_out_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions: Mapped[list[Session]] = relationship(back_populates="user", cascade="all, delete-orphan")
    invites: Mapped[list[InviteToken]] = relationship(back_populates="user", cascade="all, delete-orphan")
    password_resets: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    email_verifications: Mapped[list[EmailVerificationToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    fp_entries: Mapped[list[FoursePointsLedger]] = relationship(back_populates="user")


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_expires_at", "expires_at"),
    )

    token: Mapped[str] = mapped_column(String(64), primary_key=True)  # SHA-256 hex of session cookie
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped[User] = relationship(back_populates="sessions")


class InviteToken(Base):
    __tablename__ = "invite_tokens"
    __table_args__ = (Index("ix_invite_tokens_user_id", "user_id"),)

    token: Mapped[str] = mapped_column(String(64), primary_key=True)  # SHA-256 hex
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="invites")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (Index("ix_password_reset_tokens_user_id", "user_id"),)

    token: Mapped[str] = mapped_column(String(64), primary_key=True)  # SHA-256 hex
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="password_resets")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    __table_args__ = (Index("ix_email_verification_tokens_user_id", "user_id"),)

    token: Mapped[str] = mapped_column(String(64), primary_key=True)  # SHA-256 hex
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="email_verifications")


class StaffAuditLog(Base):
    __tablename__ = "staff_audit_logs"
    __table_args__ = (
        Index("ix_staff_audit_logs_actor_user_id", "actor_user_id"),
        Index("ix_staff_audit_logs_created_at", "created_at"),
        Index("ix_staff_audit_logs_action", "action"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FoursePointsLedger(Base):
    __tablename__ = "fourse_points_ledger"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_fp_user_event"),
        Index("ix_fp_ledger_user_id", "user_id"),
        Index("ix_fp_ledger_event_id", "event_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    placement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="fp_entries")
    event: Mapped[Event] = relationship(back_populates="fp_entries")


class CalendarAnnouncement(Base):
    __tablename__ = "calendar_announcements"
    __table_args__ = (Index("ix_calendar_announcements_event_date", "event_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PromoAction(Base):
    __tablename__ = "promo_actions"
    __table_args__ = (
        Index("ix_promo_actions_published", "published"),
        Index("ix_promo_actions_end_date", "end_date"),
        Index("ix_promo_actions_type", "type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    show_in_calendar: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    regulation_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    regulations: Mapped[list[PromoRegulationVersion]] = relationship(
        back_populates="action", cascade="all, delete-orphan"
    )
    participants: Mapped[list[PromoParticipant]] = relationship(
        back_populates="action", cascade="all, delete-orphan"
    )
    draw_result: Mapped[PromoDrawResult | None] = relationship(
        back_populates="action", cascade="all, delete-orphan", uselist=False
    )


class PromoRegulationVersion(Base):
    """Every uploaded regulation PDF is kept for audit; the highest version is current."""

    __tablename__ = "promo_regulation_versions"
    __table_args__ = (
        UniqueConstraint("promo_id", "version", name="uq_promo_regulation_version"),
        Index("ix_promo_regulation_versions_promo_id", "promo_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promo_id: Mapped[int] = mapped_column(
        ForeignKey("promo_actions.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    action: Mapped[PromoAction] = relationship(back_populates="regulations")


class PromoEnrollmentToken(Base):
    """Single-use QR token: dies on first access so the link cannot be shared."""

    __tablename__ = "promo_enrollment_tokens"
    __table_args__ = (
        Index("ix_promo_enrollment_tokens_promo_id", "promo_id"),
        Index("ix_promo_enrollment_tokens_expires_at", "expires_at"),
        Index("ix_promo_enrollment_tokens_pending_session", "pending_session_hash"),
    )

    token: Mapped[str] = mapped_column(String(64), primary_key=True)  # SHA-256 hex
    promo_id: Mapped[int] = mapped_column(
        ForeignKey("promo_actions.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pending_session_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    action: Mapped[PromoAction] = relationship()


class PromoParticipant(Base):
    __tablename__ = "promo_participants"
    __table_args__ = (
        UniqueConstraint("promo_id", "user_id", name="uq_promo_participant"),
        Index("ix_promo_participants_promo_id", "promo_id"),
        Index("ix_promo_participants_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promo_id: Mapped[int] = mapped_column(
        ForeignKey("promo_actions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=PromoParticipantStatus.pending_verification.value
    )
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    action: Mapped[PromoAction] = relationship(back_populates="participants")
    user: Mapped[User] = relationship()


class PromoDrawResult(Base):
    __tablename__ = "promo_draw_results"
    __table_args__ = (UniqueConstraint("promo_id", name="uq_promo_draw_result_promo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promo_id: Mapped[int] = mapped_column(
        ForeignKey("promo_actions.id", ondelete="CASCADE"), nullable=False
    )
    drawn_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    drawn_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    winner_count: Mapped[int] = mapped_column(Integer, nullable=False)
    winner_user_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False)

    action: Mapped[PromoAction] = relationship(back_populates="draw_result")
