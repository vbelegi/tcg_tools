import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Home } from "./Home";

function renderHome() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Home", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: "Não autenticado." }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows public shortcuts when logged out", async () => {
    renderHome();
    expect(screen.getByRole("link", { name: /torneios/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /ranking fp/i })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByRole("link", { name: /premiação/i })).not.toBeInTheDocument();
    });
    expect(screen.queryByRole("link", { name: /sorteador/i })).not.toBeInTheDocument();
  });

  it("shows staff shortcuts when authenticated as admin", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        if (String(input).includes("/auth/me")) {
          return new Response(
            JSON.stringify({
              id: 1,
              email: "admin@local",
              display_name: "Admin",
              role: "admin",
              status: "active",
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response("{}", { status: 200 });
      }),
    );
    renderHome();
    await waitFor(() => expect(screen.getByRole("link", { name: /premiação/i })).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /sorteador/i })).toBeInTheDocument();
  });
});
