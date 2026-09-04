"""Scryfall card image cache by normalized English name."""

from alembic import op
import sqlalchemy as sa

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scryfall_card_cache",
        sa.Column("name_key", sa.String(200), primary_key=True),
        sa.Column("found", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("scryfall_id", sa.String(64), nullable=True),
        sa.Column("printed_name", sa.String(200), nullable=True),
        sa.Column("image_normal", sa.String(512), nullable=True),
        sa.Column("image_small", sa.String(512), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("scryfall_card_cache")
