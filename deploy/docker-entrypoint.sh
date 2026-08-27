#!/bin/sh
set -eu

echo "Waiting for database..."
python - <<'PY'
import os
import sys
import time

url = os.environ.get("TCGTOOLS_DATABASE_URL") or ""
if not url or url.startswith("sqlite"):
    print("SQLite or empty URL; skip wait.")
    sys.exit(0)

from sqlalchemy import create_engine, text

deadline = time.time() + int(os.environ.get("TCGTOOLS_DB_WAIT_SEC", "60"))
last_err = None
while time.time() < deadline:
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        print("Database is ready.")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        last_err = exc
        time.sleep(2)

print(f"Database not ready: {last_err}", file=sys.stderr)
sys.exit(1)
PY

echo "Running migrations..."
python - <<'PY'
from app.db.init_db import init_db

init_db()
print("Migrations OK.")
PY

if [ -n "${TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD:-}" ]; then
  echo "Bootstrapping admin if missing..."
  TCGTOOLS_SET_ADMIN_PASSWORD="$TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD" \
    python -m app.scripts.bootstrap_admin || true
fi

exec "$@"
