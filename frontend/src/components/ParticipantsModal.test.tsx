import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ParticipantsModal } from "./ParticipantsModal";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    listPromoParticipants: vi.fn(),
  },
}));

describe("ParticipantsModal", () => {
  beforeEach(() => {
    vi.mocked(api.listPromoParticipants).mockReset();
  });

  it("lists display names and status only", async () => {
    vi.mocked(api.listPromoParticipants).mockResolvedValue([
      {
        id: 1,
        user_id: 11,
        display_name: "Ana",
        status: "confirmed",
        registered_at: "2026-09-03T12:00:00Z",
      },
      {
        id: 2,
        user_id: 12,
        display_name: "Bruno",
        status: "pending_verification",
        registered_at: "2026-09-03T12:05:00Z",
      },
    ]);
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <ParticipantsModal open actionId={8} onClose={() => undefined} />
      </QueryClientProvider>,
    );

    expect(await screen.findByText("Ana")).toBeInTheDocument();
    expect(screen.getByText("Confirmado")).toBeInTheDocument();
    expect(screen.getByText("Bruno")).toBeInTheDocument();
    expect(screen.getByText("Pendente (e-mail)")).toBeInTheDocument();
    expect(screen.queryByText(/@/)).not.toBeInTheDocument();
  });
});
