import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RegulationUploadField } from "./RegulationUploadField";
import { api } from "../api/client";
import type { PromoAction } from "../api/types";

vi.mock("../api/client", () => ({
  api: {
    uploadPromoRegulation: vi.fn(),
  },
}));

const uploaded: PromoAction = {
  id: 1,
  name: "Pré-venda Booster Box",
  type: "raffle_purchase_right",
  type_label: "Sorteio de Direito de Compra Físico",
  start_date: "2026-09-01",
  end_date: "2026-09-15",
  description: null,
  published: false,
  show_in_calendar: true,
  max_participants: null,
  regulation: {
    version: 1,
    display_name: "Pré-venda Booster Box v1",
    url: "/api/v1/media/acoes/1/regulamento",
  },
  created_at: null,
  regulation_versions: [
    {
      version: 1,
      display_name: "Pré-venda Booster Box v1",
      url: "/api/v1/media/acoes/1/regulamento/1",
    },
  ],
};

describe("RegulationUploadField", () => {
  beforeEach(() => {
    vi.mocked(api.uploadPromoRegulation).mockReset();
  });

  it("states that the regulation is a PDF upload, not a link", () => {
    render(
      <RegulationUploadField actionId={1} current={null} onUploaded={vi.fn()} />,
    );

    expect(screen.getByLabelText("Regulamento (PDF)")).toBeInTheDocument();
    expect(screen.getByText(/não é um link/i)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Ver regulamento/ })).not.toBeInTheDocument();
  });

  it("shows the derived display name after a successful upload", async () => {
    vi.mocked(api.uploadPromoRegulation).mockResolvedValue(uploaded);
    const onUploaded = vi.fn();

    const { rerender } = render(
      <RegulationUploadField actionId={1} current={null} onUploaded={onUploaded} />,
    );

    const file = new File(["%PDF-1.4"], "qualquer-nome.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Regulamento (PDF)"), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(onUploaded).toHaveBeenCalledWith(uploaded);
    });

    rerender(
      <RegulationUploadField
        actionId={1}
        current={uploaded.regulation}
        history={uploaded.regulation_versions}
        onUploaded={onUploaded}
      />,
    );

    const link = screen.getByRole("link", {
      name: "Ver regulamento (Pré-venda Booster Box v1)",
    });
    expect(link).toHaveAttribute("href", "/api/v1/media/acoes/1/regulamento");
  });
});
