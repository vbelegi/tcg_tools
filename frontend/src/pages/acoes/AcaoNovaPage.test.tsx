import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AcaoNovaPage } from "./AcaoNovaPage";
import { api } from "../../api/client";

vi.mock("../../api/client", () => ({
  api: {
    listPromoActionTypes: vi.fn(),
    createPromoAction: vi.fn(),
  },
}));

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AcaoNovaPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AcaoNovaPage", () => {
  beforeEach(() => {
    vi.mocked(api.listPromoActionTypes).mockReset();
    vi.mocked(api.createPromoAction).mockReset();
    vi.mocked(api.listPromoActionTypes).mockResolvedValue([
      { key: "raffle_purchase_right", label: "Sorteio de Direito de Compra Físico" },
    ]);
  });

  it("defaults calendar on and public off, and locks the type after picking the only option", async () => {
    renderPage();

    expect(await screen.findByLabelText("Exibir no calendário")).toBeChecked();
    expect(screen.getByLabelText("Pública")).not.toBeChecked();
    expect(screen.getByText(/não pode ser alterado depois/)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByLabelText("Tipo")).toHaveValue("raffle_purchase_right");
    });
  });

  it("creates the action with the form values", async () => {
    vi.mocked(api.createPromoAction).mockResolvedValue({
      id: 7,
      name: "Pré-venda",
      type: "raffle_purchase_right",
      type_label: "Sorteio de Direito de Compra Físico",
      start_date: "2026-09-01",
      end_date: "2026-09-15",
      description: null,
      published: false,
      show_in_calendar: true,
      max_participants: null,
      regulation: null,
      created_at: null,
    });

    renderPage();
    await waitFor(() => {
      expect(screen.getByLabelText("Tipo")).toHaveValue("raffle_purchase_right");
    });

    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Pré-venda" } });
    fireEvent.click(screen.getByRole("button", { name: "Criar" }));

    await waitFor(() => {
      expect(api.createPromoAction).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Pré-venda",
          type: "raffle_purchase_right",
          published: false,
          show_in_calendar: true,
          max_participants: null,
        }),
      );
    });
  });
});
