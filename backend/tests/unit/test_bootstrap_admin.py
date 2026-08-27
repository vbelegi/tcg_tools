"""Bootstrap admin script behavior."""

from __future__ import annotations

import os

from app.core.auth import get_admin, upsert_admin_password
from app.core.auth.passwords import ADMIN_EMAIL
from app.db.session import SessionLocal


def test_bootstrap_skips_when_admin_has_password(monkeypatch):
    db = SessionLocal()
    try:
        upsert_admin_password(db, "abcdef")
        admin = get_admin(db)
        assert admin is not None
        assert admin.password_hash
        old_hash = admin.password_hash

        monkeypatch.setenv("TCGTOOLS_SET_ADMIN_PASSWORD", "newpassword1")
        from app.scripts import bootstrap_admin

        assert bootstrap_admin.main() == 0
        db.expire_all()
        again = get_admin(db)
        assert again is not None
        assert again.password_hash == old_hash
        assert again.email == ADMIN_EMAIL
    finally:
        db.close()
        os.environ.pop("TCGTOOLS_SET_ADMIN_PASSWORD", None)


def test_bootstrap_requires_password(monkeypatch):
    monkeypatch.delenv("TCGTOOLS_SET_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    from app.scripts import bootstrap_admin

    assert bootstrap_admin.main() == 1
