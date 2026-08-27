"""Create admin@local only when missing (Docker/VPS bootstrap).

Uses TCGTOOLS_SET_ADMIN_PASSWORD (or argv via set_admin_password helpers).
Does not overwrite an existing admin password.
"""

from __future__ import annotations

import os
import sys


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

    from app.core.auth import get_admin, upsert_admin_password
    from app.core.auth.passwords import AuthError, MIN_PASSWORD_LEN
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        admin = get_admin(db)
        if admin is not None and admin.password_hash:
            print("Admin já existe; bootstrap ignorado.")
            return 0
        upsert_admin_password(db, password)
        print("Admin criado/atualizado (bootstrap).")
        return 0
    except AuthError as exc:
        print(f"Erro: {exc} (mínimo {MIN_PASSWORD_LEN} caracteres).", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
