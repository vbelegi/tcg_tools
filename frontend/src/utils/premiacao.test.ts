import { describe, expect, it } from "vitest";

import {
  creditosSanityMismatch,
  expectedTotalCreditos,
  sumCreditosFromRows,
} from "./premiacao";

describe("premiacao utils", () => {
  it("sums player payout credits", () => {
    const sum = sumCreditosFromRows(null, [{ payout: 2 }, { payout: 1 }], 35);
    expect(sum).toBe(105);
  });

  it("detects credit mismatch", () => {
    expect(creditosSanityMismatch(140, 100)).toBe(true);
    expect(creditosSanityMismatch(140, 140)).toBe(false);
  });

  it("computes expected total", () => {
    expect(expectedTotalCreditos(4, 35)).toBe(140);
  });

  it("sums tier creditos array", () => {
    expect(sumCreditosFromRows([70, 35], undefined, 35)).toBe(105);
  });
});
