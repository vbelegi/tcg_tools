"""Dedupe display names and enforce uniqueness (case-insensitive, non-deleted)."""

from collections import defaultdict

from alembic import op
import sqlalchemy as sa

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, display_name FROM users "
            "WHERE status != 'deleted' "
            "ORDER BY id ASC"
        )
    ).fetchall()

    by_key: dict[str, list[tuple[int, str]]] = defaultdict(list)
    taken: set[str] = set()
    for user_id, display_name in rows:
        raw = (display_name or "").strip() or "Jogador"
        key = raw.casefold()
        by_key[key].append((int(user_id), raw))
        taken.add(key)

    for key, group in by_key.items():
        if len(group) < 2:
            continue
        # Keep oldest (lowest id); rename the rest to base_1, base_2, …
        base = group[0][1]
        for idx, (user_id, _original) in enumerate(group[1:], start=1):
            n = idx
            while True:
                candidate = f"{base}_{n}"
                ckey = candidate.casefold()
                if ckey not in taken:
                    taken.add(ckey)
                    conn.execute(
                        sa.text("UPDATE users SET display_name = :name WHERE id = :id"),
                        {"name": candidate, "id": user_id},
                    )
                    break
                n += 1

    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_display_name_ci "
            "ON users (lower(display_name)) "
            "WHERE status != 'deleted'"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS uq_users_display_name_ci"))
