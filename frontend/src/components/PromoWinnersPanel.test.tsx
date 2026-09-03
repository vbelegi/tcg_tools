import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PromoWinnersPanel } from "./PromoWinnersPanel";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    listPromoWinners: vi.fn(),
    exportPromoWinnersCsv: vi.fn(),
  },
}));

describe("PromoWinnersPanel", () => {
  it("lists contemplados and offers CSV export", async () => {
    vi.mocked(api.listPromoWinners).mockResolvedValue({
      mode: "direct",
      winner_count: 1,
      drawn_at: "2026-09-03T12:00:00Z",
      winners: [{ user_id: 11, display_name: "Ana" }],
    });
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <PromoWinnersPanel actionId={3} />
      </QueryClientProvider>,
    );

    expect(await screen.findByText("Ana")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Exportar CSV" })).toBeInTheDocument();
  });
});
