"""Session tokens stored as SHA-256 hashes; invalidate existing sessions."""

import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Plaintext tokens cannot be migrated; users must log in again after deploy.
    op.execute(sa.text("DELETE FROM sessions"))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM sessions"))
