import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CalendarPage } from "./CalendarPage";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    authMe: vi.fn(),
    getCalendar: vi.fn(),
  },
}));

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <CalendarPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CalendarPage promo bands", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 8, 15));
    vi.mocked(api.authMe).mockRejectedValue(new Error("401"));
    vi.mocked(api.getCalendar).mockResolvedValue({
      tournaments: [],
      announcements: [],
      promo_actions: [
        {
          id: 9,
          name: "Pré-venda",
          start_date: "2026-09-28",
          end_date: "2026-10-05",
          description: null,
          type_label: "Sorteio de Direito de Compra Físico",
        },
      ],
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("draws a band on every clipped day of the interval", async () => {
    renderPage();
    expect(await screen.findByTestId("promo-band-9-28")).toBeInTheDocument();
    expect(screen.getByTestId("promo-band-9-29")).toBeInTheDocument();
    expect(screen.getByTestId("promo-band-9-30")).toBeInTheDocument();
    expect(screen.queryByTestId("promo-band-9-27")).not.toBeInTheDocument();
  });
});
