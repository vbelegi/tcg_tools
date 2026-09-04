"""Role hierarchy: player < staff < admin < superadmin."""

from __future__ import annotations

from app.models import User, UserRole, UserStatus
from sqlalchemy.orm import Session as DbSession

ROLE_LEVEL: dict[str, int] = {
    UserRole.player.value: 0,
    UserRole.staff.value: 1,
    UserRole.admin.value: 2,
    UserRole.superadmin.value: 3,
}

ALL_ROLES = frozenset(ROLE_LEVEL)
ADMIN_PLUS = frozenset({UserRole.admin.value, UserRole.superadmin.value})


def role_value(role: object) -> str:
    return role.value if hasattr(role, "value") else str(role)


def role_level(role: object) -> int:
    return ROLE_LEVEL.get(role_value(role), -1)


def has_min_role(user: User, minimum: str | int) -> bool:
    min_level = ROLE_LEVEL[minimum] if isinstance(minimum, str) else int(minimum)
    return role_level(user.role) >= min_level


def is_admin_plus(user: User) -> bool:
    return has_min_role(user, UserRole.admin.value)


def is_superadmin(user: User) -> bool:
    return role_value(user.role) == UserRole.superadmin.value


def count_active_superadmins(db: DbSession) -> int:
    return (
        db.query(User)
        .filter(
            User.role == UserRole.superadmin.value,
            User.status == UserStatus.active.value,
        )
        .count()
    )


def assignable_roles_for(actor: User) -> list[str]:
    """Roles the actor may assign to others."""
    if is_superadmin(actor):
        return [
            UserRole.player.value,
            UserRole.staff.value,
            UserRole.admin.value,
            UserRole.superadmin.value,
        ]
    if is_admin_plus(actor):
        return [UserRole.player.value, UserRole.staff.value]
    return []


def creatable_roles_for(actor: User) -> list[str]:
    """Roles allowed when creating an incomplete account."""
    level = role_level(actor.role)
    if level >= ROLE_LEVEL[UserRole.superadmin.value]:
        return [
            UserRole.player.value,
            UserRole.staff.value,
            UserRole.admin.value,
            UserRole.superadmin.value,
        ]
    if level >= ROLE_LEVEL[UserRole.admin.value]:
        return [UserRole.player.value, UserRole.staff.value]
    if level >= ROLE_LEVEL[UserRole.staff.value]:
        return [UserRole.player.value]
    return []
