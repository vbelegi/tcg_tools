import { describe, expect, it } from "vitest";

import { parsePastedNames } from "./pasteNames";

describe("parsePastedNames", () => {
  it("splits by newlines and commas", () => {
    expect(parsePastedNames("Alice\nBob, Carol;Dan")).toEqual([
      "Alice",
      "Bob",
      "Carol",
      "Dan",
    ]);
  });

  it("trims and drops empties", () => {
    expect(parsePastedNames("  A  \n\n  B  ")).toEqual(["A", "B"]);
  });

  it("dedupes case-insensitively preserving first casing", () => {
    expect(parsePastedNames("Alice, alice, BOB, Bob")).toEqual(["Alice", "BOB"]);
  });
});
