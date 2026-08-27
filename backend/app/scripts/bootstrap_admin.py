"""Create admin@local only when missing (Docker/VPS bootstrap).

Uses TCGTOOLS_SET_ADMIN_PASSWORD / TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD.
Does not overwrite an existing admin password.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy.orm import Session


def bootstrap_admin_if_missing(db: Session, password: str) -> str:
    """Ensure admin exists with a password. Returns 'created' or 'skipped'."""
    from app.core.auth import get_admin, upsert_admin_password

    admin = get_admin(db)
    if admin is not None and admin.password_hash:
        return "skipped"
    upsert_admin_password(db, password)
    return "created"


def main() -> int:
    password = os.environ.get("TCGTOOLS_SET_ADMIN_PASSWORD") or os.environ.get(
        "TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD"
    )
    if not password:
        print(
            "Erro: informe TCGTOOLS_SET_ADMIN_PASSWORD ou TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD.",
            file=sys.stderr,
        )
        return 1

    from app.core.auth.passwords import AuthError, MIN_PASSWORD_LEN
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        result = bootstrap_admin_if_missing(db, password)
        if result == "skipped":
            print("Admin já existe; bootstrap ignorado.")
        else:
            print("Admin criado/atualizado (bootstrap).")
        return 0
    except AuthError as exc:
        print(f"Erro: {exc} (mínimo {MIN_PASSWORD_LEN} caracteres).", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
