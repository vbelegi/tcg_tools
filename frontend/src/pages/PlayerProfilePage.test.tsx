import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PlayerProfilePage } from "./PlayerProfilePage";

const profile = {
  id: 7,
  display_name: "Jogador Teste",
  role: "player",
  status: "active",
  created_at: "2026-01-10T12:00:00",
  avatar_url: null,
  fourse_points: 120,
  fourse_points_visible: true,
  ranking_position: 2,
  can_edit: true,
  viewer_authenticated: true,
  stats: { tournaments: 2, titles: 1, top8: 2, best_finish: 1 },
  insights: ["Participa em média de 1,0 torneios por mês."],
  badge_games: [
    { id: 1, name: "Magic: The Gathering", slug: "magic", color_hex: "#f5901e" },
  ],
  fp_by_game: [
    {
      tcg_name: "Magic: The Gathering",
      tcg_game: { id: 1, name: "Magic: The Gathering", slug: "magic", color_hex: "#f5901e" },
      points: 120,
      tournaments: 2,
    },
  ],
  fp_by_month: [{ month: "2026-08", points: 120, tournaments: 2 }],
  history: [
    {
      event_id: 9,
      event_name: "Liga Semanal",
      event_date: "2026-08-20",
      source: "internal",
      rank: 1,
      rank_label: "1º",
      is_drop: false,
      decklist: "Deck A",
      player_count: 8,
      tcg_game: { id: 1, name: "Magic: The Gathering", slug: "magic", color_hex: "#f5901e" },
      fp_earned: 80,
    },
  ],
};

vi.mock("../api/client", () => ({
  api: {
    publicProfile: vi.fn(async () => profile),
    authMe: vi.fn(async () => ({ id: 7, display_name: "Jogador Teste", role: "player", status: "active" })),
    updateMe: vi.fn(),
    uploadAvatar: vi.fn(),
  },
}));

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/jogadores/7"]}>
        <Routes>
          <Route path="/jogadores/:id" element={<PlayerProfilePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("PlayerProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders stats, FP and history", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "Jogador Teste" })).toBeInTheDocument();
    expect(screen.getByText("Fourse Points")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("Liga Semanal")).toBeInTheDocument();
    expect(screen.getByText("Perfil inteligente")).toBeInTheDocument();
  });
});
