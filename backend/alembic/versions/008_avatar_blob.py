"""Store avatar WebP in users.avatar_blob; migrate files from avatar_path."""

from __future__ import annotations

import os
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def _media_root() -> Path:
    raw = os.environ.get("TCGTOOLS_DATA_DIR", "").strip()
    if raw:
        return Path(raw) / "media"
    return Path("data") / "media"


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("avatar_blob", sa.LargeBinary(), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, avatar_path FROM users WHERE avatar_path IS NOT NULL")
    ).fetchall()
    media_root = _media_root()
    for user_id, avatar_path in rows:
        if not avatar_path:
            continue
        rel = str(avatar_path).lstrip("/").removeprefix("media/")
        file_path = media_root / rel
        if not file_path.is_file():
            continue
        conn.execute(
            sa.text("UPDATE users SET avatar_blob = :blob WHERE id = :id"),
            {"blob": file_path.read_bytes(), "id": user_id},
        )

    with op.batch_alter_table("users") as batch:
        batch.drop_column("avatar_path")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("avatar_path", sa.String(255), nullable=True))
    with op.batch_alter_table("users") as batch:
        batch.drop_column("avatar_blob")
