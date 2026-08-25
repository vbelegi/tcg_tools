import { describe, expect, it } from "vitest";

import { playersMissingSeed, seedRequirementMessage } from "./seeds";

describe("playersMissingSeed", () => {
  it("returns empty when nobody has seed", () => {
    expect(
      playersMissingSeed([
        { seed: null },
        { seed: null },
      ]),
    ).toEqual([]);
  });

  it("returns empty when everyone has seed", () => {
    expect(
      playersMissingSeed([
        { seed: 1 },
        { seed: 2 },
      ]),
    ).toEqual([]);
  });

  it("lists players without seed when seeding is partial", () => {
    const missing = playersMissingSeed([
      { id: 1, seed: 1 },
      { id: 2, seed: null },
      { id: 3, seed: undefined },
    ]);
    expect(missing.map((p) => p.id)).toEqual([2, 3]);
  });
});

describe("seedRequirementMessage", () => {
  it("builds message with names", () => {
    expect(seedRequirementMessage(["Bob", "Carol"])).toMatch(/Bob, Carol/);
  });

  it("returns empty for no missing", () => {
    expect(seedRequirementMessage([])).toBe("");
  });
});
