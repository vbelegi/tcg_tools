/** Role hierarchy helpers (mirrors backend app.core.auth.roles). */

export type AppRole = "player" | "staff" | "admin" | "superadmin";

const ROLE_LEVEL: Record<string, number> = {
  player: 0,
  staff: 1,
  admin: 2,
  superadmin: 3,
};

export const ROLE_LABELS: Record<string, string> = {
  player: "Jogador",
  staff: "Staff",
  admin: "Admin",
  superadmin: "Super Admin",
};

export function roleLevel(role: string | null | undefined): number {
  if (!role) return -1;
  return ROLE_LEVEL[role] ?? -1;
}

export function hasMinRole(role: string | null | undefined, minimum: AppRole): boolean {
  return roleLevel(role) >= ROLE_LEVEL[minimum];
}

export function isStaffRole(role: string | null | undefined): boolean {
  return hasMinRole(role, "staff");
}

export function isAdminRole(role: string | null | undefined): boolean {
  return hasMinRole(role, "admin");
}

export function isSuperadminRole(role: string | null | undefined): boolean {
  return role === "superadmin";
}

export function assignableRoles(actorRole: string | null | undefined): AppRole[] {
  if (isSuperadminRole(actorRole)) {
    return ["player", "staff", "admin", "superadmin"];
  }
  if (isAdminRole(actorRole)) {
    return ["player", "staff"];
  }
  return [];
}

export function creatableRoles(actorRole: string | null | undefined): AppRole[] {
  if (isSuperadminRole(actorRole)) {
    return ["player", "staff", "admin", "superadmin"];
  }
  if (isAdminRole(actorRole)) {
    return ["player", "staff"];
  }
  if (isStaffRole(actorRole)) {
    return ["player"];
  }
  return [];
}

export function canEditUserRole(
  actorRole: string | null | undefined,
  targetRole: string,
  targetIsSelf: boolean,
): boolean {
  if (targetIsSelf) return false;
  if (isSuperadminRole(actorRole)) return true;
  if (isAdminRole(actorRole)) {
    return targetRole === "player" || targetRole === "staff";
  }
  return false;
}
