import { describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render, screen } from "@testing-library/react";
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
  it("renders navigation links to premiacao and torneios", () => {
    renderHome();
    expect(screen.getByRole("link", { name: /premiação/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /torneios/i })).toBeInTheDocument();
  });
});
