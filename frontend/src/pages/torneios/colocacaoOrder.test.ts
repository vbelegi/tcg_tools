import { describe, expect, it } from "vitest";

import { reorderPlacementRows, type PlacementRow } from "./colocacaoOrder";

const rows: PlacementRow[] = [
  { player_id: 1, name: "A", placement: "1", is_drop: false, decklist: "", deckMeta: null },
  { player_id: 2, name: "B", placement: "2", is_drop: false, decklist: "", deckMeta: null },
  { player_id: 3, name: "C", placement: "3", is_drop: false, decklist: "", deckMeta: null },
  { player_id: 4, name: "D", placement: "", is_drop: true, decklist: "", deckMeta: null },
];

describe("reorderPlacementRows", () => {
  it("moves ranked row and renumbers placements", () => {
    const next = reorderPlacementRows(rows, 2, 0);
    expect(next.map((r) => r.name)).toEqual(["C", "A", "B", "D"]);
    expect(next[0].placement).toBe("1");
    expect(next[1].placement).toBe("2");
    expect(next[2].placement).toBe("3");
    expect(next[3].is_drop).toBe(true);
  });

  it("returns original when indices invalid", () => {
    expect(reorderPlacementRows(rows, -1, 0)).toEqual(rows);
  });
});
