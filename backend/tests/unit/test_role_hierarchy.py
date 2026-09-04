"""Role hierarchy helpers — Super Admin must inherit staff/admin visibility."""

from __future__ import annotations

from types import SimpleNamespace

from app.api.v1.event_visibility import is_staff_user
from app.core.auth.roles import (
    assignable_roles_for,
    creatable_roles_for,
    has_min_role,
    is_admin_plus,
    is_superadmin,
)
from app.models import UserRole
from app.services.profile_service import can_view_fp


def _user(*, user_id: int = 1, role: str) -> SimpleNamespace:
    return SimpleNamespace(id=user_id, role=role)


def test_superadmin_is_staff_and_admin_plus():
    sa = _user(role=UserRole.superadmin.value)
    assert is_staff_user(sa) is True
    assert is_admin_plus(sa) is True
    assert is_superadmin(sa) is True
    assert has_min_role(sa, UserRole.staff.value) is True
    assert has_min_role(sa, UserRole.admin.value) is True
    assert has_min_role(sa, UserRole.superadmin.value) is True


def test_player_is_not_staff():
    player = _user(role=UserRole.player.value)
    assert is_staff_user(player) is False
    assert is_admin_plus(player) is False
    assert is_staff_user(None) is False


def test_can_view_fp_for_superadmin_viewer():
    subject = _user(user_id=10, role=UserRole.player.value)
    admin = _user(user_id=2, role=UserRole.admin.value)
    superadmin = _user(user_id=3, role=UserRole.superadmin.value)
    staff = _user(user_id=4, role=UserRole.staff.value)
    stranger = _user(user_id=5, role=UserRole.player.value)

    assert can_view_fp(None, subject) is False
    assert can_view_fp(subject, subject) is True
    assert can_view_fp(admin, subject) is True
    assert can_view_fp(superadmin, subject) is True
    assert can_view_fp(staff, subject) is False
    assert can_view_fp(stranger, subject) is False


def test_assignable_and_creatable_include_superadmin_only_for_superadmin():
    sa = _user(role=UserRole.superadmin.value)
    admin = _user(role=UserRole.admin.value)
    staff = _user(role=UserRole.staff.value)

    assert UserRole.superadmin.value in assignable_roles_for(sa)
    assert UserRole.admin.value in assignable_roles_for(sa)
    assert UserRole.superadmin.value not in assignable_roles_for(admin)
    assert assignable_roles_for(admin) == [UserRole.player.value, UserRole.staff.value]
    assert assignable_roles_for(staff) == []

    assert UserRole.superadmin.value in creatable_roles_for(sa)
    assert creatable_roles_for(admin) == [UserRole.player.value, UserRole.staff.value]
    assert creatable_roles_for(staff) == [UserRole.player.value]
