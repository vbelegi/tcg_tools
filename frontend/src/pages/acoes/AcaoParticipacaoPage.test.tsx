import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useSearchParams } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AcaoParticipacaoPage } from "./AcaoParticipacaoPage";
import { api } from "../../api/client";
import type { PromoEnrollReason, PromoEnrollResult } from "../../api/types";

vi.mock("../../api/client", () => ({
  api: {
    authMe: vi.fn(),
    enrollPromo: vi.fn(),
    completePromoEnroll: vi.fn(),
  },
}));

const player = {
  id: 5,
  email: "player@local",
  display_name: "Player",
  role: "player",
  status: "active",
};

function SearchSpy() {
  const [params] = useSearchParams();
  return <div data-testid="search">{params.toString()}</div>;
}

function result(reason: PromoEnrollReason, extra: Partial<PromoEnrollResult> = {}): PromoEnrollResult {
  return {
    reason,
    message: `mensagem ${reason}`,
    action_id: 1,
    action_name: "Pré-venda Booster Box",
    participation_status: reason === "ok" ? "confirmed" : reason === "needs_verification" ? "pending_verification" : null,
    ...extra,
  };
}

function renderPage(token = "tok-abc") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/acoes/participar/${token}`]}>
        <Routes>
          <Route
            path="/acoes/participar/:token"
            element={
              <>
                <SearchSpy />
                <AcaoParticipacaoPage />
              </>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AcaoParticipacaoPage", () => {
  beforeEach(() => {
    vi.mocked(api.authMe).mockReset();
    vi.mocked(api.enrollPromo).mockReset();
    vi.mocked(api.completePromoEnroll).mockReset();
    vi.mocked(api.authMe).mockRejectedValue(new Error("401"));
  });

  it.each([
    ["ok", "mensagem ok"],
    ["needs_verification", "mensagem needs_verification"],
    ["already_enrolled", "mensagem already_enrolled"],
    ["full", "mensagem full"],
    ["ended", "mensagem ended"],
    ["expired", "mensagem expired"],
    ["used", "mensagem used"],
    ["invalid", "mensagem invalid"],
  ] as const)("renders named reason %s", async (reason, message) => {
    vi.mocked(api.enrollPromo).mockResolvedValue(result(reason));

    renderPage();

    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pré-venda Booster Box" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ver ação promocional" })).toHaveAttribute(
      "href",
      "/acoes/1",
    );
    expect(api.completePromoEnroll).not.toHaveBeenCalled();
  });

  it("opens login for guests when the token needs auth", async () => {
    vi.mocked(api.enrollPromo).mockResolvedValue(result("needs_auth"));

    renderPage("guest-token");

    expect(await screen.findByText("mensagem needs_auth")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByTestId("search").textContent).toContain("auth=login"),
    );
    expect(screen.getByTestId("search").textContent).toContain(
      encodeURIComponent("/acoes/participar/guest-token"),
    );
    expect(api.completePromoEnroll).not.toHaveBeenCalled();
  });

  it("completes enrolment when a logged-in user still needs auth", async () => {
    vi.mocked(api.authMe).mockResolvedValue(player);
    vi.mocked(api.enrollPromo).mockResolvedValue(result("needs_auth"));
    vi.mocked(api.completePromoEnroll).mockResolvedValue(result("ok"));

    renderPage();

    expect(await screen.findByText("mensagem ok")).toBeInTheDocument();
    expect(api.completePromoEnroll).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId("search")?.textContent).not.toContain("auth=login");
  });

  it("links to e-mail verification after a pending enrolment", async () => {
    vi.mocked(api.enrollPromo).mockResolvedValue(result("needs_verification"));

    renderPage();

    expect(await screen.findByRole("link", { name: "Confirmar e-mail" })).toHaveAttribute(
      "href",
      "/conta/verificar-email",
    );
  });
});
