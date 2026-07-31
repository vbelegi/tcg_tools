import { describe, expect, it } from "vitest";

import {
  allValidScorePairs,
  isValidScorePair,
  validScoresForPlayer,
} from "./scores";

describe("isValidScorePair", () => {
  it("allows 1-0 time win in bo3", () => {
    expect(isValidScorePair(1, 0, 3, false)).toBe(true);
  });

  it("allows 0-0 draw in swiss bo3", () => {
    expect(isValidScorePair(0, 0, 3, true)).toBe(true);
  });

  it("rejects draw in elimination", () => {
    expect(isValidScorePair(0, 0, 3, false)).toBe(false);
  });

  it("rejects 3-0 in bo3", () => {
    expect(isValidScorePair(3, 0, 3, false)).toBe(false);
  });
});

describe("validScoresForPlayer", () => {
  it("lists p1 options for bo1 elimination", () => {
    expect(validScoresForPlayer(1, false, 1, undefined)).toEqual([0, 1]);
  });

  it("lists p1 options for bo3 without 3", () => {
    expect(validScoresForPlayer(3, false, 1, undefined)).toEqual([0, 1, 2]);
  });

  it("lists p1 options for bo5 up to 3", () => {
    expect(validScoresForPlayer(5, false, 1, undefined)).toEqual([0, 1, 2, 3]);
  });

  it("filters p2 when p1 is set in bo3", () => {
    expect(validScoresForPlayer(3, false, 2, 1)).toEqual([0, 2]);
    expect(validScoresForPlayer(3, false, 2, 2)).toEqual([0, 1]);
  });

  it("includes draw scores for swiss", () => {
    const pairs = allValidScorePairs(3, true);
    expect(pairs.some((p) => p.p1 === 0 && p.p2 === 0)).toBe(true);
    expect(pairs.some((p) => p.p1 === 1 && p.p2 === 1)).toBe(true);
  });
});
