import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { PlayerPickerModal } from "./PlayerPickerModal";

describe("PlayerPickerModal", () => {
  it("confirms selected player", () => {
    const onConfirm = vi.fn();
    render(
      <PlayerPickerModal
        open
        title="Pick"
        description="Choose"
        players={[{ id: 1, name: "Alice" }]}
        onConfirm={onConfirm}
        onClose={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    expect(onConfirm).toHaveBeenCalledWith(1);
  });

  it("requires typing the player name before confirming when requireNameConfirm", () => {
    const onConfirm = vi.fn();
    render(
      <PlayerPickerModal
        open
        title="Drop"
        description="Irreversible"
        players={[
          { id: 1, name: "Belegi" },
          { id: 2, name: "Agatha" },
        ]}
        confirmLabel="Confirmar drop"
        requireNameConfirm
        onConfirm={onConfirm}
        onClose={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("Jogador"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));

    const nameInput = screen.getByLabelText("Digite o nome do jogador");
    const confirmBtn = screen.getByRole("button", { name: "Confirmar drop" });
    expect(confirmBtn).toBeDisabled();

    fireEvent.change(nameInput, { target: { value: "errado" } });
    expect(confirmBtn).toBeDisabled();
    expect(onConfirm).not.toHaveBeenCalled();

    fireEvent.change(nameInput, { target: { value: "belegi" } });
    expect(confirmBtn).not.toBeDisabled();
    fireEvent.click(confirmBtn);
    expect(onConfirm).toHaveBeenCalledWith(1);
  });

  it("allows going back from name confirm step", () => {
    render(
      <PlayerPickerModal
        open
        title="Drop"
        description="Irreversible"
        players={[{ id: 1, name: "Belegi" }]}
        requireNameConfirm
        onConfirm={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    expect(screen.getByLabelText("Digite o nome do jogador")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Voltar" }));
    expect(screen.getByLabelText("Jogador")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continuar" })).toBeInTheDocument();
  });
});
