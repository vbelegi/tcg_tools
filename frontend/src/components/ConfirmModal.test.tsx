import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { ConfirmModal } from "./ConfirmModal";

describe("ConfirmModal", () => {
  it("calls onConfirm when confirm clicked", () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmModal
        open
        title="Test"
        message="Sure?"
        confirmLabel="OK"
        onClose={vi.fn()}
        onConfirm={onConfirm}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(onConfirm).toHaveBeenCalled();
  });
});
