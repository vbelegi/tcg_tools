import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AgendaPage } from "./AgendaPage";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    listCalendarAnnouncements: vi.fn(),
    createCalendarAnnouncement: vi.fn(),
    updateCalendarAnnouncement: vi.fn(),
    deleteCalendarAnnouncement: vi.fn(),
  },
}));

function renderPage(initial = "/agenda") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial]}>
        <AgendaPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AgendaPage filters", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date(2026, 8, 15));
    vi.mocked(api.listCalendarAnnouncements).mockReset();
    vi.mocked(api.listCalendarAnnouncements).mockResolvedValue([
      {
        id: 1,
        title: "Pré-release",
        event_date: "2026-09-10",
        description: null,
        start_time: "19:00",
        location: "Loja",
      },
    ]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("defaults the date range to the current month", async () => {
    renderPage();
    expect(await screen.findByText("Pré-release")).toBeInTheDocument();
    expect(api.listCalendarAnnouncements).toHaveBeenCalledWith({
      q: undefined,
      from: "2026-09-01",
      to: "2026-09-30",
    });
  });

  it("passes title search to the API after debounce", async () => {
    renderPage();
    await screen.findByText("Pré-release");

    fireEvent.change(screen.getByLabelText("Buscar por título"), {
      target: { value: "pré" },
    });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    await waitFor(() => {
      expect(api.listCalendarAnnouncements).toHaveBeenLastCalledWith({
        q: "pré",
        from: "2026-09-01",
        to: "2026-09-30",
      });
    });
  });
});
