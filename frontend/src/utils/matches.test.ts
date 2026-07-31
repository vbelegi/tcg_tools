import { describe, expect, it } from "vitest";

import type { Match } from "../api/types";
import {
  formatMatchResult,
  incompleteMatches,
  isMatchIncomplete,
  matchSummaryLabel,
} from "./matches";

const baseMatch: Match = {
  id: 1,
  player1_id: 1,
  player1_name: "Alice",
  player2_id: 2,
  player2_name: "Bob",
  winner_id: null,
  score_p1: 0,
  score_p2: 0,
  is_bye: false,
  is_walkover: false,
  had_rematch: false,
  scores_submitted: false,
};

describe("isMatchIncomplete", () => {
  it("flags normal match without saved score", () => {
    expect(isMatchIncomplete(baseMatch)).toBe(true);
  });

  it("ignores saved and special matches", () => {
    expect(isMatchIncomplete({ ...baseMatch, scores_submitted: true })).toBe(false);
    expect(isMatchIncomplete({ ...baseMatch, is_bye: true })).toBe(false);
    expect(isMatchIncomplete({ ...baseMatch, is_walkover: true })).toBe(false);
  });
});

describe("match helpers", () => {
  it("lists incomplete matches", () => {
    const saved = { ...baseMatch, id: 2, scores_submitted: true };
    expect(incompleteMatches([baseMatch, saved])).toHaveLength(1);
  });

  it("formats labels and results", () => {
    expect(matchSummaryLabel(baseMatch)).toBe("Alice × Bob");
    expect(matchSummaryLabel({ ...baseMatch, is_bye: true })).toBe("BYE — Alice");
    expect(matchSummaryLabel({ ...baseMatch, is_walkover: true })).toBe("Alice × Bob");
    expect(formatMatchResult({ ...baseMatch, scores_submitted: true, score_p1: 2, score_p2: 0 })).toBe(
      "2–0",
    );
    expect(formatMatchResult({ ...baseMatch, is_bye: true })).toBe("BYE");
  });
});
