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

    dialect = conn.dialect.name
    if dialect == "mysql":
        # MySQL has no partial indexes; NULL keys are unique-friendly so deleted
        # accounts can share ANONYMOUS_DISPLAY_NAME without colliding.
        op.execute(
            sa.text(
                "ALTER TABLE users ADD COLUMN display_name_key VARCHAR(120) "
                "GENERATED ALWAYS AS ("
                "CASE WHEN status = 'deleted' THEN NULL ELSE LOWER(display_name) END"
                ") STORED"
            )
        )
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX uq_users_display_name_ci ON users (display_name_key)"
            )
        )
    else:
        # SQLite / Postgres: partial unique index excludes deleted rows.
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_display_name_ci "
                "ON users (lower(display_name)) "
                "WHERE status != 'deleted'"
            )
        )


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect == "mysql":
        op.execute(sa.text("DROP INDEX uq_users_display_name_ci ON users"))
        op.execute(sa.text("ALTER TABLE users DROP COLUMN display_name_key"))
    else:
        op.execute(sa.text("DROP INDEX IF EXISTS uq_users_display_name_ci"))
