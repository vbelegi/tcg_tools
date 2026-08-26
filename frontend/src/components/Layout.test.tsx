import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen, waitFor } from "@testing-library/react";

import { Layout } from "./Layout";

describe("Layout", () => {
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

  it("renders public sidebar navigation when logged out", async () => {
    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <Layout />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(screen.getByText("Torneios")).toBeInTheDocument();
    expect(screen.getByText("Ranking FP")).toBeInTheDocument();
    expect(screen.queryByText("Premiação")).not.toBeInTheDocument();
    expect(screen.queryByText("Alterar senha")).not.toBeInTheDocument();
    expect(screen.getByText("Powered by")).toBeInTheDocument();
    expect(screen.getByText("FOURSE")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "Entrar" })).toBeInTheDocument());
  });

  it("shows staff links when authenticated as admin", async () => {
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
        return new Response("{}", { status: 200 });
      }),
    );
    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <Layout />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(screen.getByText("Premiação")).toBeInTheDocument());
    expect(screen.getByText("Usuários")).toBeInTheDocument();
    expect(screen.getByText("Meu Perfil")).toBeInTheDocument();
    expect(screen.queryByText("Alterar senha")).not.toBeInTheDocument();
  });
});
