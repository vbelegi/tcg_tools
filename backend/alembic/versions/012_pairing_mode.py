"""Event pairing_mode (platform vs manual placements)."""

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("pairing_mode", sa.String(16), nullable=False, server_default="platform"),
    )


def downgrade() -> None:
    op.drop_column("events", "pairing_mode")
