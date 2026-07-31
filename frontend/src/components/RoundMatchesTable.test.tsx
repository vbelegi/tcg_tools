import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { RoundMatchesTable } from "./RoundMatchesTable";

describe("RoundMatchesTable", () => {
  it("renders bronze and Bo labels", () => {
    render(
      <RoundMatchesTable
        matches={[
          {
            id: 1,
            player1_id: 1,
            player1_name: "A",
            player2_id: 2,
            player2_name: "B",
            winner_id: 1,
            score_p1: 2,
            score_p2: 0,
            is_bye: false,
            is_walkover: false,
            had_rematch: false,
            is_third_place: true,
            best_of: 5,
          },
        ]}
      />,
    );
    expect(screen.getByText("3º–4º")).toBeInTheDocument();
    expect(screen.getByText("Bo5")).toBeInTheDocument();
  });

  it("renders walkover separator", () => {
    render(
      <RoundMatchesTable
        matches={[
          {
            id: 3,
            player1_id: 1,
            player1_name: "Augusto",
            player2_id: 2,
            player2_name: "P2",
            winner_id: 1,
            score_p1: 2,
            score_p2: 0,
            is_bye: false,
            is_walkover: true,
            had_rematch: false,
          },
        ]}
      />,
    );
    expect(screen.getByText("×")).toBeInTheDocument();
    expect(screen.getByText("2–0 (WO)")).toBeInTheDocument();
  });

  it("renders bye row", () => {
    render(
      <RoundMatchesTable
        matches={[
          {
            id: 2,
            player1_id: 1,
            player1_name: "A",
            player2_id: null,
            player2_name: null,
            winner_id: 1,
            score_p1: 1,
            score_p2: 0,
            is_bye: true,
            is_walkover: false,
            had_rematch: false,
          },
        ]}
      />,
    );
    expect(screen.getAllByText(/BYE/).length).toBeGreaterThan(0);
  });
});
