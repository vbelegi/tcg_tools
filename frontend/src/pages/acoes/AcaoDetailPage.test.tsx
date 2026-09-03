import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AcaoDetailPage } from "./AcaoDetailPage";
import { api } from "../../api/client";
import { todayIso } from "./promoFormat";

vi.mock("../../api/client", () => ({
  api: {
    authMe: vi.fn(),
    getPromoAction: vi.fn(),
    publishPromoAction: vi.fn(),
    uploadPromoRegulation: vi.fn(),
    updatePromoAction: vi.fn(),
    listPromoParticipants: vi.fn(),
    listPromoLogs: vi.fn(),
    createPromoEnrollmentToken: vi.fn(),
  },
}));

const shiftDays = (days: number) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return todayIso(d);
};

const action = {
  id: 1,
  name: "Pré-venda Booster Box",
  type: "raffle_purchase_right",
  type_label: "Sorteio de Direito de Compra Físico",
  start_date: shiftDays(-2),
  end_date: shiftDays(12),
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
    expect(screen.queryByRole("button", { name: "Editar Ação" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Inscrever Novo Participante" })).not.toBeInTheDocument();
  });

  it("shows a green participation box when the player is confirmed", async () => {
    vi.mocked(api.authMe).mockResolvedValue({
      id: 5,
      email: "player@local",
      display_name: "Player",
      role: "player",
      status: "active",
    });
    vi.mocked(api.getPromoAction).mockResolvedValue({
      ...action,
      my_participation: { status: "confirmed" },
    });

    renderPage();

    expect(
      await screen.findByText("Você já está participando desta Ação Promocional."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/necessário ter uma conta/)).not.toBeInTheDocument();
  });

  it("tells a pending player to confirm e-mail", async () => {
    vi.mocked(api.authMe).mockResolvedValue({
      id: 5,
      email: "player@local",
      display_name: "Player",
      role: "player",
      status: "active",
    });
    vi.mocked(api.getPromoAction).mockResolvedValue({
      ...action,
      my_participation: { status: "pending_verification" },
    });

    renderPage();

    expect(await screen.findByText(/Inscrição pendente; confirme seu e-mail/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Reenviar link de verificação" })).toHaveAttribute(
      "href",
      "/conta/verificar-email",
    );
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
    expect(screen.getByRole("button", { name: "Editar Ação" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inscrever Novo Participante" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Exibir Lista de Participantes" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Logs da Ação" })).not.toBeInTheDocument();
  });

  it("shows logs to admin and blocks a new QR after the action ended", async () => {
    vi.mocked(api.authMe).mockResolvedValue({
      id: 1,
      email: "admin@local",
      display_name: "Admin",
      role: "admin",
      status: "active",
    });
    vi.mocked(api.getPromoAction).mockResolvedValue({
      ...action,
      start_date: shiftDays(-20),
      end_date: shiftDays(-2),
      participant_count: 2,
      regulation_versions: [],
    });

    renderPage();

    expect(await screen.findByRole("button", { name: "Logs da Ação" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inscrever Novo Participante" })).toBeDisabled();
    expect(screen.getByText(/não é possível gerar um novo QR/i)).toBeInTheDocument();
  });

  it("shows a friendly message when the action is not visible", async () => {
    vi.mocked(api.authMe).mockRejectedValue(new Error("401"));
    vi.mocked(api.getPromoAction).mockRejectedValue(new Error("Ação não encontrada."));

    renderPage();

    expect(await screen.findByRole("heading", { name: "Ação não encontrada" })).toBeInTheDocument();
  });
});
