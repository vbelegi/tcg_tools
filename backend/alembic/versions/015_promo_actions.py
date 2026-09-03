"""Promotional actions: actions, versioned regulations, enrollment tokens, participants, draws."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "promo_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("max_participants", sa.Integer(), nullable=True),
        sa.Column("show_in_calendar", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("regulation_version", sa.Integer(), nullable=True),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_promo_actions_published", "promo_actions", ["published"])
    op.create_index("ix_promo_actions_end_date", "promo_actions", ["end_date"])
    op.create_index("ix_promo_actions_type", "promo_actions", ["type"])

    op.create_table(
        "promo_regulation_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "promo_id",
            sa.Integer(),
            sa.ForeignKey("promo_actions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("stored_name", sa.String(255), nullable=False),
        sa.Column(
            "uploaded_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("promo_id", "version", name="uq_promo_regulation_version"),
    )
    op.create_index(
        "ix_promo_regulation_versions_promo_id", "promo_regulation_versions", ["promo_id"]
    )

    op.create_table(
        "promo_enrollment_tokens",
        sa.Column("token", sa.String(64), primary_key=True),
        sa.Column(
            "promo_id",
            sa.Integer(),
            sa.ForeignKey("promo_actions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("pending_session_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_promo_enrollment_tokens_promo_id", "promo_enrollment_tokens", ["promo_id"])
    op.create_index(
        "ix_promo_enrollment_tokens_expires_at", "promo_enrollment_tokens", ["expires_at"]
    )
    op.create_index(
        "ix_promo_enrollment_tokens_pending_session",
        "promo_enrollment_tokens",
        ["pending_session_hash"],
    )

    op.create_table(
        "promo_participants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "promo_id",
            sa.Integer(),
            sa.ForeignKey("promo_actions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("promo_id", "user_id", name="uq_promo_participant"),
    )
    op.create_index("ix_promo_participants_promo_id", "promo_participants", ["promo_id"])
    op.create_index("ix_promo_participants_user_id", "promo_participants", ["user_id"])

    op.create_table(
        "promo_draw_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "promo_id",
            sa.Integer(),
            sa.ForeignKey("promo_actions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("drawn_at", sa.DateTime(), nullable=False),
        sa.Column(
            "drawn_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("winner_count", sa.Integer(), nullable=False),
        sa.Column("winner_user_ids", sa.JSON(), nullable=False),
        sa.UniqueConstraint("promo_id", name="uq_promo_draw_result_promo"),
    )


def downgrade() -> None:
    op.drop_table("promo_draw_results")
    op.drop_index("ix_promo_participants_user_id", table_name="promo_participants")
    op.drop_index("ix_promo_participants_promo_id", table_name="promo_participants")
    op.drop_table("promo_participants")
    op.drop_index(
        "ix_promo_enrollment_tokens_pending_session", table_name="promo_enrollment_tokens"
    )
    op.drop_index("ix_promo_enrollment_tokens_expires_at", table_name="promo_enrollment_tokens")
    op.drop_index("ix_promo_enrollment_tokens_promo_id", table_name="promo_enrollment_tokens")
    op.drop_table("promo_enrollment_tokens")
    op.drop_index(
        "ix_promo_regulation_versions_promo_id", table_name="promo_regulation_versions"
    )
    op.drop_table("promo_regulation_versions")
    op.drop_index("ix_promo_actions_type", table_name="promo_actions")
    op.drop_index("ix_promo_actions_end_date", table_name="promo_actions")
    op.drop_index("ix_promo_actions_published", table_name="promo_actions")
    op.drop_table("promo_actions")
