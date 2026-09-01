import { describe, expect, it } from "vitest";

import { safeRedirectPath } from "./safeRedirect";

describe("safeRedirectPath", () => {
  it("accepts relative paths", () => {
    expect(safeRedirectPath("/torneios/1")).toBe("/torneios/1");
    expect(safeRedirectPath("/calendario")).toBe("/calendario");
  });

  it("rejects external and protocol-relative URLs", () => {
    expect(safeRedirectPath("//evil.com")).toBeNull();
    expect(safeRedirectPath("https://evil.com")).toBeNull();
    expect(safeRedirectPath("http://evil.com/path")).toBeNull();
    expect(safeRedirectPath("/\\evil")).toBeNull();
  });

  it("rejects empty and non-path values", () => {
    expect(safeRedirectPath("")).toBeNull();
    expect(safeRedirectPath("torneios")).toBeNull();
    expect(safeRedirectPath(null)).toBeNull();
  });
});
