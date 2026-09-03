import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PromoRafflePanel } from "./PromoRafflePanel";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    listPromoParticipants: vi.fn(),
    drawPromoAction: vi.fn(),
  },
}));

function renderPanel() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onDrawn = vi.fn();
  render(
    <QueryClientProvider client={qc}>
      <PromoRafflePanel actionId={3} onDrawn={onDrawn} />
    </QueryClientProvider>,
  );
  return onDrawn;
}

describe("PromoRafflePanel", () => {
  beforeEach(() => {
    vi.mocked(api.listPromoParticipants).mockReset();
    vi.mocked(api.drawPromoAction).mockReset();
    vi.mocked(api.listPromoParticipants).mockResolvedValue([
      {
        id: 1,
        user_id: 11,
        display_name: "Ana",
        status: "confirmed",
        registered_at: null,
      },
      {
        id: 2,
        user_id: 12,
        display_name: "Bruno",
        status: "confirmed",
        registered_at: null,
      },
    ]);
    vi.mocked(api.drawPromoAction).mockResolvedValue({
      mode: "direct",
      winner_count: 1,
      drawn_at: "2026-09-03T12:00:00Z",
      winners: [{ user_id: 11, display_name: "Ana" }],
    });
  });

  it("persists a direct draw on the server", async () => {
    const onDrawn = renderPanel();

    expect(await screen.findByText(/Pool confirmada: 2/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Sortear" }));

    await waitFor(() => expect(api.drawPromoAction).toHaveBeenCalled());
    expect(api.drawPromoAction).toHaveBeenCalledWith(3, { mode: "direct", winner_count: 1 });
    expect(onDrawn).toHaveBeenCalled();
  });
});
