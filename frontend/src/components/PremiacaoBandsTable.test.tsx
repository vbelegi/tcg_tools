import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PremiacaoBandsTable } from "./PremiacaoBandsTable";

describe("PremiacaoBandsTable", () => {
  it("renders player payouts with credits", () => {
    render(
      <PremiacaoBandsTable
        bands={[{ label: "1º", pool: 2, payout_per_player: 2 }]}
        playerPayouts={[
          { player_id: 1, name: "Alice", band_label: "1º", payout: 2 },
          { player_id: 2, name: "Bob", band_label: "2º", payout: 1 },
        ]}
        entryFee={35}
      />,
    );
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("R$ 70.00")).toBeInTheDocument();
  });

  it("renders band preview rows", () => {
    render(
      <PremiacaoBandsTable
        bands={[
          { label: "1º", pool: 2, payout_per_player: 2 },
          { label: "2º", pool: 1, payout_per_player: null },
        ]}
        bandCreditos={[70, 35]}
        entryFee={35}
      />,
    );
    expect(screen.getByText("1º")).toBeInTheDocument();
    expect(screen.getByText("R$ 70.00")).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });
});
