import { describe, expect, it } from "vitest";

import {
  assignableRoles,
  canEditUserRole,
  creatableRoles,
  hasMinRole,
  isAdminRole,
  isStaffRole,
} from "./roles";

describe("roles", () => {
  it("treats superadmin as admin+", () => {
    expect(isAdminRole("superadmin")).toBe(true);
    expect(isStaffRole("superadmin")).toBe(true);
    expect(hasMinRole("admin", "admin")).toBe(true);
    expect(hasMinRole("staff", "admin")).toBe(false);
  });

  it("limits assignable roles by actor", () => {
    expect(assignableRoles("admin")).toEqual(["player", "staff"]);
    expect(assignableRoles("superadmin")).toContain("admin");
    expect(assignableRoles("superadmin")).toContain("superadmin");
  });

  it("gates role editing", () => {
    expect(canEditUserRole("admin", "player", false)).toBe(true);
    expect(canEditUserRole("admin", "admin", false)).toBe(false);
    expect(canEditUserRole("superadmin", "admin", false)).toBe(true);
    expect(canEditUserRole("superadmin", "player", true)).toBe(false);
  });

  it("limits creatable roles", () => {
    expect(creatableRoles("staff")).toEqual(["player"]);
    expect(creatableRoles("admin")).toEqual(["player", "staff"]);
    expect(creatableRoles("superadmin")).toEqual(["player", "staff", "admin", "superadmin"]);
  });
});
