import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { RaffleResultModal } from "./RaffleResultModal";

describe("RaffleResultModal", () => {
  it("lists winners and redraws in batch mode", () => {
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

  it("shows chain actions", () => {
    const onDrawNext = vi.fn();
    render(
      <RaffleResultModal
        open
        mode="chain"
        winners={["Alice"]}
        remainingCount={2}
        onClose={vi.fn()}
        onDrawNext={onDrawNext}
        onRestartChain={vi.fn()}
      />,
    );
    expect(screen.getByText("Sorteio encadeado")).toBeInTheDocument();
    expect(screen.getByText(/Sorteado agora:/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Sortear próximo" }));
    expect(onDrawNext).toHaveBeenCalled();
  });

  it("draws next with Enter in chain mode", () => {
    const onDrawNext = vi.fn();
    render(
      <RaffleResultModal
        open
        mode="chain"
        winners={["Alice"]}
        remainingCount={1}
        onClose={vi.fn()}
        onDrawNext={onDrawNext}
      />,
    );
    fireEvent.keyDown(document.body, { key: "Enter" });
    expect(onDrawNext).toHaveBeenCalled();
  });

  it("shows empty state", () => {
    render(<RaffleResultModal open winners={[]} onClose={vi.fn()} />);
    expect(screen.getByText("Nenhum sorteado.")).toBeInTheDocument();
  });
});
