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
});
