import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MatchBadges } from "./MatchBadges";

describe("MatchBadges", () => {
  it("shows bronze badge for third-place match", () => {
    render(<MatchBadges match={{ is_third_place: true } as never} />);
    expect(screen.getByText("3º–4º")).toBeInTheDocument();
  });

  it("renders nothing for a normal match", () => {
    const { container } = render(
      <MatchBadges match={{ is_third_place: false } as never} />,
    );
    expect(container.textContent).toBe("");
  });
});
