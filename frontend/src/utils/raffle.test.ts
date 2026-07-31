import { describe, expect, it } from "vitest";

import { drawWinners, shuffle } from "./raffle";

describe("shuffle", () => {
  it("returns a permutation of the input", () => {
    const input = [1, 2, 3, 4, 5];
    const out = shuffle(input, () => 0.5);
    expect(out.sort()).toEqual(input);
    expect(out).not.toBe(input);
  });
});

describe("drawWinners", () => {
  it("draws unique winners", () => {
    const names = ["A", "B", "C", "D", "E"];
    const winners = drawWinners(names, 3);
    expect(winners).toHaveLength(3);
    expect(new Set(winners).size).toBe(3);
    winners.forEach((w) => expect(names).toContain(w));
  });

  it("rejects empty pool", () => {
    expect(() => drawWinners([], 1)).toThrow(/participante/i);
  });

  it("rejects too many winners", () => {
    expect(() => drawWinners(["A", "B"], 3)).toThrow(/maior que participantes/i);
  });
});
