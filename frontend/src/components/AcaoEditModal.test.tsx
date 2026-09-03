import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AcaoEditModal } from "./AcaoEditModal";
import { api } from "../api/client";
import type { PromoAction } from "../api/types";

vi.mock("../api/client", () => ({
  api: {
    updatePromoAction: vi.fn(),
  },
}));

const action: PromoAction = {
  id: 1,
  name: "Pré-venda Booster Box",
  type: "raffle_purchase_right",
  type_label: "Sorteio de Direito de Compra Físico",
  start_date: "2026-09-01",
  end_date: "2026-09-15",
  description: "Direito de compra.",
  published: false,
  show_in_calendar: true,
  max_participants: null,
  regulation: null,
  created_at: null,
};

function renderModal() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onSaved = vi.fn();
  const onClose = vi.fn();
  render(
    <QueryClientProvider client={qc}>
      <AcaoEditModal open action={action} onClose={onClose} onSaved={onSaved} />
    </QueryClientProvider>,
  );
  return { onSaved, onClose };
}

describe("AcaoEditModal", () => {
  beforeEach(() => {
    vi.mocked(api.updatePromoAction).mockReset();
    vi.mocked(api.updatePromoAction).mockResolvedValue({ ...action, name: "Nome Novo" });
  });

  it("locks the type and saves the editable fields", async () => {
    const { onSaved, onClose } = renderModal();

    const typeField = screen.getByLabelText("Tipo");
    expect(typeField).toBeDisabled();
    expect(typeField).toHaveValue("Sorteio de Direito de Compra Físico");
    expect(screen.getByLabelText("Pública")).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Nome Novo" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => expect(api.updatePromoAction).toHaveBeenCalled());
    expect(api.updatePromoAction).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        name: "Nome Novo",
        start_date: "2026-09-01",
        end_date: "2026-09-15",
        show_in_calendar: true,
        max_participants: null,
      }),
    );
    const body = vi.mocked(api.updatePromoAction).mock.calls[0][1];
    expect(body).not.toHaveProperty("type");
    expect(body).not.toHaveProperty("published");
    expect(onSaved).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });
});
