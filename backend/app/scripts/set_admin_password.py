"""CLI: set or reset admin password (used by installer)."""

from __future__ import annotations

import argparse
import os
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Define a senha do usuário admin no SQLite.")
    parser.add_argument(
        "--password",
        default=None,
        help="Senha em texto. Prefira TCGTOOLS_SET_ADMIN_PASSWORD no ambiente.",
    )
    args = parser.parse_args(argv)

    password = args.password or os.environ.get("TCGTOOLS_SET_ADMIN_PASSWORD")
    if not password:
        print("Erro: informe --password ou TCGTOOLS_SET_ADMIN_PASSWORD.", file=sys.stderr)
        return 2

    # Ensure DB / migrations
    from app.db.init_db import init_db
    from app.db.session import SessionLocal
    from app.core.auth import upsert_admin_password
    from app.core.auth.passwords import AuthError, MIN_PASSWORD_LEN

    try:
        init_db()
        db = SessionLocal()
        try:
            upsert_admin_password(db, password)
        finally:
            db.close()
    except AuthError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Senha do admin atualizada (mínimo {MIN_PASSWORD_LEN} caracteres).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
