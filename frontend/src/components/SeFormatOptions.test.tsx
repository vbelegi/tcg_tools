import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SeFormatOptions } from "./SeFormatOptions";

describe("SeFormatOptions", () => {
  it("renders phases for 16 players (4 rounds)", () => {
    render(
      <SeFormatOptions
        thirdPlaceMatch={false}
        onThirdPlaceMatchChange={vi.fn()}
        seBoConfig={{}}
        onSeBoConfigChange={vi.fn()}
        defaultBestOf={3}
        maxRounds={4}
      />,
    );
    expect(screen.getByText("Final (incl. bronze)")).toBeInTheDocument();
    expect(screen.getByText("Oitavas")).toBeInTheDocument();
  });

  it("toggles third place match", () => {
    const onThird = vi.fn();
    render(
      <SeFormatOptions
        thirdPlaceMatch={false}
        onThirdPlaceMatchChange={onThird}
        seBoConfig={{}}
        onSeBoConfigChange={vi.fn()}
        defaultBestOf={3}
        maxRounds={2}
      />,
    );
    fireEvent.click(screen.getByRole("checkbox"));
    expect(onThird).toHaveBeenCalledWith(true);
  });

  it("updates phase Bo config", () => {
    const onBo = vi.fn();
    render(
      <SeFormatOptions
        thirdPlaceMatch={false}
        onThirdPlaceMatchChange={vi.fn()}
        seBoConfig={{}}
        onSeBoConfigChange={onBo}
        defaultBestOf={3}
        maxRounds={2}
      />,
    );
    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[0], { target: { value: "5" } });
    expect(onBo).toHaveBeenCalledWith({ "2": 5 });
  });
});
