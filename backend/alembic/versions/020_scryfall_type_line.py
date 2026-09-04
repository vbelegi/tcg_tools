"""Scryfall cache: type_line + image_large for deck grouping / zoom."""

from alembic import op
import sqlalchemy as sa

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scryfall_card_cache", sa.Column("type_line", sa.String(200), nullable=True))
    op.add_column("scryfall_card_cache", sa.Column("image_large", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("scryfall_card_cache", "image_large")
    op.drop_column("scryfall_card_cache", "type_line")
