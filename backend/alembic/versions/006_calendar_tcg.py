"""TCG games catalog, event description/start_time, open registration default."""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

SEED_GAMES = [
    ("Magic: The Gathering", "magic", "#f5901e"),
    ("Pokémon TCG", "pokemon", "#FFCB05"),
    ("Yu-Gi-Oh!", "yugioh", "#9a0056"),
    ("One Piece CG", "one-piece", "#58acf4"),
    ("Digimon CG", "digimon", "#FFD700"),
    ("Disney Lorcana", "lorcana", "#0189C4"),
    ("Riftbound", "riftbound", "#458b74"),
]


def upgrade() -> None:
    op.create_table(
        "tcg_games",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("color_hex", sa.String(7), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("slug", name="uq_tcg_games_slug"),
        sa.UniqueConstraint("name", name="uq_tcg_games_name"),
    )

    for name, slug, color in SEED_GAMES:
        op.execute(
            sa.text(
                "INSERT INTO tcg_games (name, slug, color_hex, active, created_at) "
                "VALUES (:name, :slug, :color, 1, CURRENT_TIMESTAMP)"
            ).bindparams(name=name, slug=slug, color=color)
        )

    with op.batch_alter_table("events") as batch:
        batch.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch.add_column(sa.Column("start_time", sa.String(5), nullable=True))
        batch.add_column(sa.Column("tcg_game_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_events_tcg_game_id",
            "tcg_games",
            ["tcg_game_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.alter_column(
            "registration_open",
            existing_type=sa.Boolean(),
            server_default="1",
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("events") as batch:
        batch.drop_constraint("fk_events_tcg_game_id", type_="foreignkey")
        batch.drop_column("tcg_game_id")
        batch.drop_column("start_time")
        batch.drop_column("description")
        batch.alter_column(
            "registration_open",
            existing_type=sa.Boolean(),
            server_default="0",
            existing_nullable=False,
        )
    op.drop_table("tcg_games")
