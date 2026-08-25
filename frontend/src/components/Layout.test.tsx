import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";

import { Layout } from "./Layout";

describe("Layout", () => {
  it("renders sidebar navigation", () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <Layout />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(screen.getByText("Premiação")).toBeInTheDocument();
    expect(screen.getByText("Torneios")).toBeInTheDocument();
    expect(screen.getByText("Alterar senha")).toBeInTheDocument();
    expect(screen.getByText("Powered by")).toBeInTheDocument();
    expect(screen.getByText("FOURSE")).toBeInTheDocument();
  });
});
