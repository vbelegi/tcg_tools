"""Promote bootstrap admin@local to Super Admin (role is a free string)."""

from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE users SET role = 'superadmin' "
        "WHERE email = 'admin@local' AND role = 'admin'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE users SET role = 'admin' "
        "WHERE email = 'admin@local' AND role = 'superadmin'"
    )
