import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";

import { TorneiosListPage } from "./TorneiosListPage";
import { api } from "../../api/client";

vi.mock("../../api/client", () => ({
  api: {
    authMe: vi.fn(),
    listTorneios: vi.fn(),
  },
}));

const draft = {
  id: 1,
  name: "Liga Semanal",
  event_date: "2026-09-10",
  format: "swiss" as const,
  max_rounds: 3,
  entry_fee: 35,
  best_of: 3,
  status: "draft" as const,
  player_count: 4,
  current_round: 0,
  registration_open: true,
};

const finished = {
  ...draft,
  id: 2,
  name: "Final de Temporada",
  event_date: "2026-08-01",
  status: "finished" as const,
  registration_open: false,
};

function renderPage(initial = "/torneios") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial]}>
        <TorneiosListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("TorneiosListPage filters", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.mocked(api.authMe).mockReset();
    vi.mocked(api.listTorneios).mockReset();
    vi.mocked(api.authMe).mockResolvedValue({
      id: 1,
      email: "admin@local",
      display_name: "Admin",
      role: "admin",
      status: "active",
    } as never);
    vi.mocked(api.listTorneios).mockResolvedValue([draft, finished]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("loads with empty filters and lists tournaments", async () => {
    renderPage();
    expect(await screen.findByText("Liga Semanal")).toBeInTheDocument();
    expect(screen.getByText("Final de Temporada")).toBeInTheDocument();
    expect(api.listTorneios).toHaveBeenCalledWith({
      q: undefined,
      active: undefined,
      from: undefined,
      to: undefined,
    });
  });

  it("passes search, dates and active toggle to the API", async () => {
    renderPage();
    await screen.findByText("Liga Semanal");

    fireEvent.change(screen.getByLabelText("Buscar por nome"), {
      target: { value: "liga" },
    });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    fireEvent.change(screen.getByLabelText("De"), { target: { value: "2026-09-01" } });
    fireEvent.change(screen.getByLabelText("Até"), { target: { value: "2026-09-30" } });
    fireEvent.click(screen.getByRole("switch", { name: "Somente não encerrados" }));

    await waitFor(() => {
      expect(api.listTorneios).toHaveBeenLastCalledWith({
        q: "liga",
        active: true,
        from: "2026-09-01",
        to: "2026-09-30",
      });
    });
  });
});
