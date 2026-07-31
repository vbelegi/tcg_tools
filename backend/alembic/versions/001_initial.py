"""Initial schema."""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("format", sa.String(32), nullable=False),
        sa.Column("max_rounds", sa.Integer(), nullable=True),
        sa.Column("entry_fee", sa.Float(), nullable=False),
        sa.Column("best_of", sa.Integer(), nullable=False),
        sa.Column("premiacao_preset", sa.JSON(), nullable=False),
        sa.Column("premiacao_resultado", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("shuffle_seed", sa.Integer(), nullable=True),
    )
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("dropped_at", sa.DateTime(), nullable=True),
        sa.Column("registration_order", sa.Integer(), nullable=False),
        sa.Column("decklist", sa.Text(), nullable=True),
    )
    op.create_index("ix_players_event_id", "players", ["event_id"])
    op.create_table(
        "rounds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
    )
    op.create_index("ix_rounds_event_id", "rounds", ["event_id"])
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("round_id", sa.Integer(), sa.ForeignKey("rounds.id"), nullable=False),
        sa.Column("player1_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("player2_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=True),
        sa.Column("winner_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=True),
        sa.Column("score_p1", sa.Integer(), nullable=False),
        sa.Column("score_p2", sa.Integer(), nullable=False),
        sa.Column("is_bye", sa.Boolean(), nullable=False),
        sa.Column("is_walkover", sa.Boolean(), nullable=False),
        sa.Column("had_rematch", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_matches_round_id", "matches", ["round_id"])
    op.create_index("ix_matches_player1_id", "matches", ["player1_id"])
    op.create_index("ix_matches_player2_id", "matches", ["player2_id"])


def downgrade() -> None:
    op.drop_table("matches")
    op.drop_table("rounds")
    op.drop_table("players")
    op.drop_table("events")
