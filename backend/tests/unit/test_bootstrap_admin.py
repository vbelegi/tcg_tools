"""Bootstrap admin script behavior."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.auth import get_admin, upsert_admin_password
from app.core.auth.passwords import ADMIN_EMAIL
from app.scripts.bootstrap_admin import bootstrap_admin_if_missing, main


def test_bootstrap_skips_when_admin_has_password(db_session: Session):
    upsert_admin_password(db_session, "abcdefgh12")
    admin = get_admin(db_session)
    assert admin is not None
    assert admin.password_hash
    old_hash = admin.password_hash

    assert bootstrap_admin_if_missing(db_session, "newpassword1") == "skipped"
    db_session.expire_all()
    again = get_admin(db_session)
    assert again is not None
    assert again.password_hash == old_hash
    assert again.email == ADMIN_EMAIL


def test_bootstrap_creates_when_missing(db_session: Session):
    assert get_admin(db_session) is None or not (get_admin(db_session).password_hash or "")
    # Fresh migrated DB may have no admin row
    assert bootstrap_admin_if_missing(db_session, "abcdefgh12") == "created"
    admin = get_admin(db_session)
    assert admin is not None
    assert admin.email == ADMIN_EMAIL
    assert admin.password_hash


def test_bootstrap_requires_password(monkeypatch):
    monkeypatch.delenv("TCGTOOLS_SET_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("TCGTOOLS_BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    assert main() == 1
