"""Scryfall cache: back-face images for DFC / MDFC flip."""

from alembic import op
import sqlalchemy as sa

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scryfall_card_cache", sa.Column("layout", sa.String(32), nullable=True))
    op.add_column("scryfall_card_cache", sa.Column("printed_name_back", sa.String(200), nullable=True))
    op.add_column("scryfall_card_cache", sa.Column("image_normal_back", sa.String(512), nullable=True))
    op.add_column("scryfall_card_cache", sa.Column("image_small_back", sa.String(512), nullable=True))
    op.add_column("scryfall_card_cache", sa.Column("image_large_back", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("scryfall_card_cache", "image_large_back")
    op.drop_column("scryfall_card_cache", "image_small_back")
    op.drop_column("scryfall_card_cache", "image_normal_back")
    op.drop_column("scryfall_card_cache", "printed_name_back")
    op.drop_column("scryfall_card_cache", "layout")
