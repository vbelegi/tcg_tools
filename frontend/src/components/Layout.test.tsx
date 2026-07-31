import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";

import { Layout } from "./Layout";

describe("Layout", () => {
  it("renders sidebar navigation", () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>,
    );
    expect(screen.getByText("Premiação")).toBeInTheDocument();
    expect(screen.getByText("Torneios")).toBeInTheDocument();
  });
});
