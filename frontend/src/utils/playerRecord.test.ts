import { describe, expect, it } from "vitest";

import { formatPlayerRecord, playerRecordTitle } from "./playerRecord";

describe("formatPlayerRecord", () => {
  it("formats wins/losses/draws", () => {
    expect(formatPlayerRecord({ wins: 2, losses: 1, draws: 0 })).toBe("2/1/0");
  });

  it("defaults missing record to 0/0/0", () => {
    expect(formatPlayerRecord(undefined)).toBe("0/0/0");
  });
});

describe("playerRecordTitle", () => {
  it("includes W/L/D label", () => {
    expect(playerRecordTitle({ wins: 1, losses: 0, draws: 1 })).toContain("W/L/D: 1/0/1");
  });
});
