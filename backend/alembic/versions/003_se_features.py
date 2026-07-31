"""SE features: third_place_match, se_bo_config, match metadata."""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("third_place_match", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column("events", sa.Column("se_bo_config", sa.JSON(), nullable=True))
    op.add_column(
        "matches",
        sa.Column("is_third_place", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column("matches", sa.Column("best_of", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "best_of")
    op.drop_column("matches", "is_third_place")
    op.drop_column("events", "se_bo_config")
    op.drop_column("events", "third_place_match")
