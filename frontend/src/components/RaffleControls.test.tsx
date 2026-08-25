import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { RaffleControls } from "./RaffleControls";

describe("RaffleControls", () => {
  it("runs batch draw", () => {
    render(<RaffleControls participants={["Alice", "Bob", "Carol"]} />);
    fireEvent.change(screen.getByLabelText("Número de sorteados"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Sortear" }));
    expect(screen.getByText("Resultado do sorteio")).toBeInTheDocument();
    expect(screen.getAllByText(/Sorteado \d/).length).toBe(2);
  });

  it("runs chained draws without repeating", () => {
    render(<RaffleControls participants={["Alice", "Bob"]} />);
    fireEvent.click(screen.getByLabelText(/Encadeado/i));
    fireEvent.click(screen.getByRole("button", { name: "Sortear o 1º" }));
    expect(screen.getByText("Sorteio encadeado")).toBeInTheDocument();
    expect(screen.getByText(/Sorteado agora:/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Sortear próximo" }));
    expect(screen.getByText(/Restam 0/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Sortear próximo" })).not.toBeInTheDocument();
  });

  it("disables draw when pool is empty", () => {
    render(<RaffleControls participants={[]} />);
    expect(screen.getByRole("button", { name: "Sortear" })).toBeDisabled();
  });
});

describe("RaffleControls chain restart", () => {
  it("resets chain from modal", () => {
    const spy = vi.spyOn(Math, "random").mockReturnValue(0);
    render(<RaffleControls participants={["Alice", "Bob", "Carol"]} />);
    fireEvent.click(screen.getByLabelText(/Encadeado/i));
    fireEvent.click(screen.getByRole("button", { name: "Sortear o 1º" }));
    fireEvent.click(screen.getByRole("button", { name: "Reiniciar" }));
    expect(screen.queryByText("Sorteio encadeado")).not.toBeInTheDocument();
    spy.mockRestore();
  });
});
