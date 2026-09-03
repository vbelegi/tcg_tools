"""Purge incomplete accounts older than retention window (default 180 days)."""

from __future__ import annotations

import argparse
import sys

from app.core.auth.account_lifecycle import purge_stale_incomplete
from app.core.privacy import INCOMPLETE_PURGE_DAYS
from app.db.session import SessionLocal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Anonimizar incomplete sem claim após N dias")
    parser.add_argument("--days", type=int, default=INCOMPLETE_PURGE_DAYS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    db = SessionLocal()
    try:
        if args.dry_run:
            from datetime import datetime, timedelta

            from app.models import User, UserStatus

            cutoff = datetime.utcnow() - timedelta(days=args.days)
            ids = [
                u.id
                for u in db.query(User)
                .filter(User.status == UserStatus.incomplete.value, User.created_at < cutoff)
                .all()
            ]
            print(f"dry-run: {len(ids)} incomplete user(s) would be purged: {ids}")
            return 0
        ids = purge_stale_incomplete(db, days=args.days)
        print(f"purged {len(ids)} incomplete user(s): {ids}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
