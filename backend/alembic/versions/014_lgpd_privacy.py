"""LGPD: privacy acceptance, marketing opt-out, deleted status, audit log, hashed invites."""

from __future__ import annotations

import hashlib

from alembic import op
import sqlalchemy as sa

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def upgrade() -> None:
    op.add_column("users", sa.Column("privacy_accepted_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("privacy_policy_version", sa.String(16), nullable=True))
    op.add_column("users", sa.Column("terms_version", sa.String(16), nullable=True))
    op.add_column(
        "users",
        sa.Column("marketing_opt_out", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column("users", sa.Column("marketing_opt_out_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("marketing_opt_out_source", sa.String(32), nullable=True))

    op.create_table(
        "staff_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_staff_audit_logs_actor_user_id", "staff_audit_logs", ["actor_user_id"])
    op.create_index("ix_staff_audit_logs_created_at", "staff_audit_logs", ["created_at"])
    op.create_index("ix_staff_audit_logs_action", "staff_audit_logs", ["action"])

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT token FROM invite_tokens")).fetchall()
    for (token,) in rows:
        if token is None:
            continue
        # Already SHA-256 hex (64 chars) — leave as-is
        if len(token) == 64 and all(c in "0123456789abcdef" for c in token.lower()):
            continue
        hashed = _hash_token(token)
        conn.execute(
            sa.text("UPDATE invite_tokens SET token = :h WHERE token = :t"),
            {"h": hashed, "t": token},
        )


def downgrade() -> None:
    op.drop_index("ix_staff_audit_logs_action", table_name="staff_audit_logs")
    op.drop_index("ix_staff_audit_logs_created_at", table_name="staff_audit_logs")
    op.drop_index("ix_staff_audit_logs_actor_user_id", table_name="staff_audit_logs")
    op.drop_table("staff_audit_logs")
    op.drop_column("users", "marketing_opt_out_source")
    op.drop_column("users", "marketing_opt_out_at")
    op.drop_column("users", "marketing_opt_out")
    op.drop_column("users", "terms_version")
    op.drop_column("users", "privacy_policy_version")
    op.drop_column("users", "privacy_accepted_at")
