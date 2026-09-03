import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AcaoDetailPage } from "./AcaoDetailPage";
import { api } from "../../api/client";

vi.mock("../../api/client", () => ({
  api: {
    authMe: vi.fn(),
    getPromoAction: vi.fn(),
    publishPromoAction: vi.fn(),
    uploadPromoRegulation: vi.fn(),
  },
}));

const action = {
  id: 1,
  name: "Pré-venda Booster Box",
  type: "raffle_purchase_right",
  type_label: "Sorteio de Direito de Compra Físico",
  start_date: "2026-09-01",
  end_date: "2026-09-15",
  description: "Direito de compra do produto limitado.",
  published: true,
  show_in_calendar: true,
  max_participants: null,
  regulation: null,
  created_at: null,
  how_to_participate: "A inscrição é presencial. Vá até a loja durante o período da ação.",
  management_panel_key: "raffle_purchase_right",
};

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/acoes/1"]}>
        <Routes>
          <Route path="/acoes/:id" element={<AcaoDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AcaoDetailPage", () => {
  beforeEach(() => {
    vi.mocked(api.authMe).mockReset();
    vi.mocked(api.getPromoAction).mockReset();
  });

  it("tells guests they need an account to take part", async () => {
    vi.mocked(api.authMe).mockRejectedValue(new Error("401"));
    vi.mocked(api.getPromoAction).mockResolvedValue(action);

    renderPage();

    expect(await screen.findByText(/necessário ter uma conta e estar logado/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Criar conta" })).toBeInTheDocument();
    expect(screen.getByText(/A inscrição é presencial/)).toBeInTheDocument();
  });

  it("does not offer publishing or upload to players", async () => {
    vi.mocked(api.authMe).mockResolvedValue({
      id: 5,
      email: "player@local",
      display_name: "Player",
      role: "player",
      status: "active",
    });
    vi.mocked(api.getPromoAction).mockResolvedValue(action);

    renderPage();

    expect(await screen.findByRole("heading", { name: "Pré-venda Booster Box" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "← Ações Promocionais" })).toHaveAttribute(
      "href",
      "/acoes",
    );
    expect(screen.queryByRole("button", { name: "Publicar" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Regulamento (PDF)")).not.toBeInTheDocument();
    expect(screen.queryByText(/necessário ter uma conta/)).not.toBeInTheDocument();
  });

  it("offers publishing and regulation upload to staff on a draft", async () => {
    vi.mocked(api.authMe).mockResolvedValue({
      id: 9,
      email: "staff@local",
      display_name: "Staff",
      role: "staff",
      status: "active",
    });
    vi.mocked(api.getPromoAction).mockResolvedValue({
      ...action,
      published: false,
      participant_count: 0,
      regulation_versions: [],
    });

    renderPage();

    expect(await screen.findByRole("button", { name: "Publicar" })).toBeInTheDocument();
    expect(screen.getByLabelText("Regulamento (PDF)")).toBeInTheDocument();
    expect(screen.getByText("rascunho")).toBeInTheDocument();
  });

  it("shows a friendly message when the action is not visible", async () => {
    vi.mocked(api.authMe).mockRejectedValue(new Error("401"));
    vi.mocked(api.getPromoAction).mockRejectedValue(new Error("Ação não encontrada."));

    renderPage();

    expect(await screen.findByRole("heading", { name: "Ação não encontrada" })).toBeInTheDocument();
  });
});
