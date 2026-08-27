"""Users roles/profile, invites, attendance, FP ledger, external events."""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("email", sa.String(255), nullable=True))
        batch.add_column(sa.Column("display_name", sa.String(120), nullable=True))
        batch.add_column(sa.Column("phone", sa.String(32), nullable=True))
        batch.add_column(sa.Column("birth_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("guardian_name", sa.String(120), nullable=True))
        batch.add_column(sa.Column("guardian_phone", sa.String(32), nullable=True))
        batch.add_column(sa.Column("guardian_relation", sa.String(64), nullable=True))
        batch.add_column(sa.Column("role", sa.String(16), nullable=False, server_default="admin"))
        batch.add_column(sa.Column("status", sa.String(16), nullable=False, server_default="active"))
        batch.alter_column("password_hash", existing_type=sa.String(255), nullable=True)
        batch.alter_column("username", existing_type=sa.String(64), nullable=True)

    op.execute(
        """
        UPDATE users SET
          email = COALESCE(email, CONCAT(LOWER(username), '@local')),
          display_name = COALESCE(display_name, username),
          role = 'admin',
          status = 'active'
        WHERE email IS NULL OR display_name IS NULL
        """
        if op.get_bind().dialect.name != "sqlite"
        else """
        UPDATE users SET
          email = COALESCE(email, lower(username) || '@local'),
          display_name = COALESCE(display_name, username),
          role = 'admin',
          status = 'active'
        WHERE email IS NULL OR display_name IS NULL
        """
    )

    with op.batch_alter_table("users") as batch:
        batch.alter_column("email", existing_type=sa.String(255), nullable=False)
        batch.alter_column("display_name", existing_type=sa.String(120), nullable=False)
        batch.create_unique_constraint("uq_users_email", ["email"])
        batch.create_unique_constraint("uq_users_phone", ["phone"])

    with op.batch_alter_table("players") as batch:
        batch.add_column(
            sa.Column("attendance", sa.String(16), nullable=False, server_default="checked_in")
        )
        batch.add_column(
            sa.Column("registration_source", sa.String(16), nullable=False, server_default="staff")
        )

    with op.batch_alter_table("events") as batch:
        batch.add_column(
            sa.Column("source", sa.String(16), nullable=False, server_default="internal")
        )
        batch.add_column(sa.Column("registration_open", sa.Boolean(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("fp_n_at_start", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("external_notes", sa.Text(), nullable=True))

    op.create_table(
        "invite_tokens",
        sa.Column("token", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_invite_tokens_user_id", "invite_tokens", ["user_id"])

    op.create_table(
        "fourse_points_ledger",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("placement", sa.Integer(), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "event_id", name="uq_fp_user_event"),
    )
    op.create_index("ix_fp_ledger_user_id", "fourse_points_ledger", ["user_id"])
    op.create_index("ix_fp_ledger_event_id", "fourse_points_ledger", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_fp_ledger_event_id", table_name="fourse_points_ledger")
    op.drop_index("ix_fp_ledger_user_id", table_name="fourse_points_ledger")
    op.drop_table("fourse_points_ledger")
    op.drop_index("ix_invite_tokens_user_id", table_name="invite_tokens")
    op.drop_table("invite_tokens")

    with op.batch_alter_table("events") as batch:
        batch.drop_column("external_notes")
        batch.drop_column("fp_n_at_start")
        batch.drop_column("registration_open")
        batch.drop_column("source")

    with op.batch_alter_table("players") as batch:
        batch.drop_column("registration_source")
        batch.drop_column("attendance")

    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uq_users_phone", type_="unique")
        batch.drop_constraint("uq_users_email", type_="unique")
        batch.drop_column("status")
        batch.drop_column("role")
        batch.drop_column("guardian_relation")
        batch.drop_column("guardian_phone")
        batch.drop_column("guardian_name")
        batch.drop_column("birth_date")
        batch.drop_column("phone")
        batch.drop_column("display_name")
        batch.drop_column("email")
        batch.alter_column("password_hash", existing_type=sa.String(255), nullable=False)
        batch.alter_column("username", existing_type=sa.String(64), nullable=False)
