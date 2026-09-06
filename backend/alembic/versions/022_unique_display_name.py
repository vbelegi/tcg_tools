"""Dedupe display names and enforce uniqueness (case-insensitive, non-deleted)."""

from collections import defaultdict

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def _index_names(conn, table: str) -> set[str]:
    return {idx["name"] for idx in inspect(conn).get_indexes(table)}


def _column_names(conn, table: str) -> set[str]:
    return {c["name"] for c in inspect(conn).get_columns(table)}


def _dedupe_casefold(conn) -> None:
    """SQLite / generic: group by Python casefold (matches lower() index)."""
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

    for _key, group in by_key.items():
        if len(group) < 2:
            continue
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


def _name_taken_mysql(conn, candidate: str, *, exclude_id: int) -> bool:
    """Use MySQL collation equality (case + accent insensitive with unicode_ci)."""
    row = conn.execute(
        sa.text(
            "SELECT id FROM users "
            "WHERE status != 'deleted' AND display_name = :name AND id != :id "
            "LIMIT 1"
        ),
        {"name": candidate, "id": exclude_id},
    ).fetchone()
    return row is not None


def _dedupe_mysql_collation(conn) -> None:
    """Group duplicates the way MySQL UNIQUE would (table collation)."""
    groups = conn.execute(
        sa.text(
            "SELECT display_name, COUNT(*) AS c FROM users "
            "WHERE status != 'deleted' "
            "GROUP BY display_name "
            "HAVING COUNT(*) > 1"
        )
    ).fetchall()

    for display_name, _count in groups:
        members = conn.execute(
            sa.text(
                "SELECT id, display_name FROM users "
                "WHERE status != 'deleted' AND display_name = :name "
                "ORDER BY id ASC"
            ),
            {"name": display_name},
        ).fetchall()
        if len(members) < 2:
            continue
        base = (members[0][1] or "").strip() or "Jogador"
        for idx, (user_id, _original) in enumerate(members[1:], start=1):
            n = idx
            while True:
                candidate = f"{base}_{n}"
                if not _name_taken_mysql(conn, candidate, exclude_id=int(user_id)):
                    conn.execute(
                        sa.text("UPDATE users SET display_name = :name WHERE id = :id"),
                        {"name": candidate, "id": int(user_id)},
                    )
                    break
                n += 1


def _mysql_reset_022_artifacts(conn) -> None:
    """Drop partial artifacts from failed 1.17.0 / 1.17.1 attempts (idempotent)."""
    indexes = _index_names(conn, "users")
    cols = _column_names(conn, "users")
    if "uq_users_display_name_ci" in indexes:
        op.execute(sa.text("DROP INDEX uq_users_display_name_ci ON users"))
    if "display_name_key" in cols:
        op.execute(sa.text("ALTER TABLE users DROP COLUMN display_name_key"))
    if "display_name_active" in cols:
        op.execute(sa.text("ALTER TABLE users DROP COLUMN display_name_active"))


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "mysql":
        _dedupe_mysql_collation(conn)
        _mysql_reset_022_artifacts(conn)
        # UNIQUE(display_name, active_flag): table collation handles CI;
        # NULL active_flag lets soft-deleted rows share the same name.
        op.execute(
            sa.text(
                "ALTER TABLE users ADD COLUMN display_name_active TINYINT "
                "GENERATED ALWAYS AS ("
                "CASE WHEN status = 'deleted' THEN NULL ELSE 1 END"
                ") STORED"
            )
        )
        op.execute(
            sa.text(
                "CREATE UNIQUE INDEX uq_users_display_name_ci "
                "ON users (display_name, display_name_active)"
            )
        )
    else:
        _dedupe_casefold(conn)
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
        _mysql_reset_022_artifacts(conn)
    else:
        op.execute(sa.text("DROP INDEX IF EXISTS uq_users_display_name_ci"))
