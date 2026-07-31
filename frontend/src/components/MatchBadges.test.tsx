import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MatchBadges } from "./MatchBadges";

describe("MatchBadges", () => {
  it("shows bronze and Bo badges", () => {
    render(
      <MatchBadges
        match={{ is_third_place: true } as never}
        bestOf={5}
      />,
    );
    expect(screen.getByText("3º–4º")).toBeInTheDocument();
    expect(screen.getByText("Bo5")).toBeInTheDocument();
  });

  it("hides Bo1 label", () => {
    const { container } = render(
      <MatchBadges match={{ is_third_place: false } as never} bestOf={1} />,
    );
    expect(container.textContent).toBe("");
  });
});
