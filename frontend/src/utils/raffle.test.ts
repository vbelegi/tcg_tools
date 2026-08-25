import { describe, expect, it } from "vitest";

import { drawWinners, pickOne, shuffle } from "./raffle";

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

describe("pickOne", () => {
  it("picks one and leaves the rest without duplication", () => {
    const pool = ["A", "B", "C"];
    const { picked, remaining } = pickOne(pool, () => 0);
    expect(picked).toBe("A");
    expect(remaining).toEqual(["B", "C"]);
    expect(remaining).not.toContain(picked);
    expect(remaining.length + 1).toBe(pool.length);
  });

  it("rejects empty pool", () => {
    expect(() => pickOne([])).toThrow(/não há mais/i);
  });

  it("can chain until empty without repeats", () => {
    let pool = ["A", "B", "C"];
    const drawn: string[] = [];
    while (pool.length > 0) {
      const step = pickOne(pool, () => 0);
      drawn.push(step.picked);
      pool = step.remaining;
    }
    expect(drawn.sort()).toEqual(["A", "B", "C"]);
    expect(new Set(drawn).size).toBe(3);
  });
});
