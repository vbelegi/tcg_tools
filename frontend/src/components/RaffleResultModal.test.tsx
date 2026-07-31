import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { RaffleResultModal } from "./RaffleResultModal";

describe("RaffleResultModal", () => {
  it("lists winners and redraws", () => {
    const onRedraw = vi.fn();
    render(
      <RaffleResultModal
        open
        winners={["Alice"]}
        onClose={vi.fn()}
        onRedraw={onRedraw}
      />,
    );
    expect(screen.getByText("Alice")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Sortear novamente" }));
    expect(onRedraw).toHaveBeenCalled();
  });

  it("shows empty state", () => {
    render(<RaffleResultModal open winners={[]} onClose={vi.fn()} />);
    expect(screen.getByText("Nenhum sorteado.")).toBeInTheDocument();
  });
});
