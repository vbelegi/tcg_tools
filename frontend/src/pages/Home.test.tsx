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
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/auth/me")) {
          return new Response(JSON.stringify({ detail: "Não autenticado." }), {
            status: 401,
            headers: { "Content-Type": "application/json" },
          });
        }
        if (url.includes("/ranking")) {
          return new Response(JSON.stringify([]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response("{}", { status: 200 });
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows public shortcuts when logged out", async () => {
    renderHome();
    expect(screen.getByRole("link", { name: /torneios/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /ações promocionais/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /calendário/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /ranking fourse points/i })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("link", { name: /^entrar$/i })).toBeInTheDocument();
    });
    expect(screen.queryByRole("link", { name: /premiação/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /sorteador/i })).not.toBeInTheDocument();
  });

  it("shows staff and admin shortcuts when authenticated as admin", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/auth/me")) {
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
        if (url.includes("/ranking")) {
          return new Response(
            JSON.stringify([
              {
                rank: 1,
                user_id: 2,
                display_name: "Belegi",
                points: 67,
                avatar_url: null,
              },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response("{}", { status: 200 });
      }),
    );
    renderHome();
    await waitFor(() => expect(screen.getByRole("link", { name: /premiação/i })).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /sorteador/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /novo torneio/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /usuários/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /tcgs/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /meu perfil/i })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Belegi")).toBeInTheDocument());
  });

  it("shows staff and admin shortcuts when authenticated as superadmin", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/auth/me")) {
          return new Response(
            JSON.stringify({
              id: 1,
              email: "admin@local",
              display_name: "Super Admin",
              role: "superadmin",
              status: "active",
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        if (url.includes("/ranking")) {
          return new Response(JSON.stringify([]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        return new Response("{}", { status: 200 });
      }),
    );
    renderHome();
    await waitFor(() => expect(screen.getByRole("link", { name: /premiação/i })).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /sorteador/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /usuários/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /tcgs/i })).toBeInTheDocument();
  });
});
