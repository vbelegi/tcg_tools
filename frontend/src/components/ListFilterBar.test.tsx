import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ListFilterBar } from "./ListFilterBar";

describe("ListFilterBar", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("debounces typing into a single search change", () => {
    const onSearchChange = vi.fn();
    render(
      <ListFilterBar
        searchLabel="Buscar por nome"
        searchValue=""
        onSearchChange={onSearchChange}
      />,
    );

    const input = screen.getByLabelText("Buscar por nome");
    fireEvent.change(input, { target: { value: "pre" } });
    fireEvent.change(input, { target: { value: "pre-venda" } });

    expect(onSearchChange).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(onSearchChange).toHaveBeenCalledTimes(1);
    expect(onSearchChange).toHaveBeenCalledWith("pre-venda");
  });

  it("reports toggle changes immediately", () => {
    const onChange = vi.fn();
    render(
      <ListFilterBar
        searchLabel="Buscar por nome"
        searchValue=""
        onSearchChange={vi.fn()}
        toggles={[
          { id: "active", label: "Somente ações ativas", checked: false, onChange },
        ]}
        resultCount={1}
      />,
    );

    const toggle = screen.getByRole("switch", { name: "Somente ações ativas" });
    expect(toggle).not.toBeChecked();
    fireEvent.click(toggle);

    expect(onChange).toHaveBeenCalledWith(true);
    expect(screen.getByText("1 resultado")).toBeInTheDocument();
  });
});
