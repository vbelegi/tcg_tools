import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AcoesListPage } from "./AcoesListPage";
import { api } from "../../api/client";

vi.mock("../../api/client", () => ({
  api: {
    authMe: vi.fn(),
    listPromoActions: vi.fn(),
  },
}));

const published = {
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
  regulation: {
    version: 2,
    display_name: "Pré-venda Booster Box v2",
    url: "/api/v1/media/acoes/1/regulamento",
  },
  created_at: null,
};

const draft = {
  ...published,
  id: 2,
  name: "Rascunho Interno",
  published: false,
  regulation: null,
};

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/acoes"]}>
        <AcoesListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AcoesListPage", () => {
  beforeEach(() => {
    vi.mocked(api.authMe).mockReset();
    vi.mocked(api.listPromoActions).mockReset();
  });

  it("shows the current regulation link on the card", async () => {
    vi.mocked(api.authMe).mockRejectedValue(new Error("401"));
    vi.mocked(api.listPromoActions).mockResolvedValue([published]);

    renderPage();

    const link = await screen.findByRole("link", {
      name: "Regulamento (Pré-venda Booster Box v2)",
    });
    expect(link).toHaveAttribute("href", "/api/v1/media/acoes/1/regulamento");
  });

  it("hides the create button and participant count from guests", async () => {
    vi.mocked(api.authMe).mockRejectedValue(new Error("401"));
    vi.mocked(api.listPromoActions).mockResolvedValue([published]);

    renderPage();

    await screen.findByText("Pré-venda Booster Box");
    expect(screen.queryByRole("link", { name: "Criar Ação" })).not.toBeInTheDocument();
    expect(screen.queryByText(/inscritos/)).not.toBeInTheDocument();
  });

  it("shows drafts and the create button to staff", async () => {
    vi.mocked(api.authMe).mockResolvedValue({
      id: 9,
      email: "staff@local",
      display_name: "Staff",
      role: "staff",
      status: "active",
    });
    vi.mocked(api.listPromoActions).mockResolvedValue([published, draft]);

    renderPage();

    expect(await screen.findByText("Rascunho Interno")).toBeInTheDocument();
    expect(screen.getByText("rascunho")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Criar Ação" })).toHaveAttribute(
      "href",
      "/acoes/nova",
    );
  });

  it("honours search and active filters from the query string", async () => {
    vi.mocked(api.authMe).mockRejectedValue(new Error("401"));
    vi.mocked(api.listPromoActions).mockResolvedValue([published]);

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={["/acoes?q=booster&active=1"]}>
          <AcoesListPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await screen.findByText("Pré-venda Booster Box");
    expect(api.listPromoActions).toHaveBeenCalledWith({ q: "booster", active: true });
    expect(screen.getByLabelText("Buscar por nome")).toHaveValue("booster");
    expect(screen.getByLabelText("Somente ações ativas")).toBeChecked();
  });

  it("passes the active toggle down to the API", async () => {
    vi.mocked(api.authMe).mockRejectedValue(new Error("401"));
    vi.mocked(api.listPromoActions).mockResolvedValue([published]);

    renderPage();
    await screen.findByText("Pré-venda Booster Box");

    fireEvent.click(screen.getByLabelText("Somente ações ativas"));

    await waitFor(() => {
      expect(api.listPromoActions).toHaveBeenLastCalledWith({ q: undefined, active: true });
    });
  });
});
