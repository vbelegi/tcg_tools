import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { RankingPage } from "./RankingPage";

vi.mock("../api/client", () => ({
  api: {
    ranking: vi.fn(async () => [
      { rank: 1, user_id: 1, display_name: "Belegi", points: 67, avatar_url: null },
      { rank: 2, user_id: 2, display_name: "Agatha", points: 22, avatar_url: null },
      { rank: 3, user_id: 3, display_name: "Amanda", points: 13, avatar_url: null },
      { rank: 4, user_id: 4, display_name: "Augusto", points: 9, avatar_url: null },
    ]),
  },
}));

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <RankingPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("RankingPage", () => {
  it("shows podium for top 3 and table from 4th", async () => {
    renderPage();
    expect(await screen.findByLabelText("Top 3")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Ranking Fourse Points" })).toBeInTheDocument();
    expect(screen.getAllByText("Belegi").length).toBeGreaterThan(0);
    expect(screen.getByRole("columnheader", { name: "Jogador" })).toBeInTheDocument();
    expect(screen.getByText("Augusto")).toBeInTheDocument();
  });
});
