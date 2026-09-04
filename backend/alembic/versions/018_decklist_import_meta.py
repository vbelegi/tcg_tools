"""Decklist import metadata on players (LigaMagic snapshot)."""

from alembic import op
import sqlalchemy as sa

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("players", sa.Column("decklist_source", sa.String(32), nullable=True))
    op.add_column("players", sa.Column("decklist_source_id", sa.String(64), nullable=True))
    op.add_column("players", sa.Column("decklist_source_url", sa.String(512), nullable=True))
    op.add_column("players", sa.Column("decklist_name", sa.String(200), nullable=True))
    op.add_column("players", sa.Column("decklist_format", sa.String(64), nullable=True))
    op.add_column("players", sa.Column("decklist_price_low_brl", sa.Numeric(12, 2), nullable=True))
    op.add_column("players", sa.Column("decklist_imported_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "decklist_imported_at")
    op.drop_column("players", "decklist_price_low_brl")
    op.drop_column("players", "decklist_format")
    op.drop_column("players", "decklist_name")
    op.drop_column("players", "decklist_source_url")
    op.drop_column("players", "decklist_source_id")
    op.drop_column("players", "decklist_source")
