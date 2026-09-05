import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { EnrollmentQrModal } from "./EnrollmentQrModal";
import { api } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    createPromoEnrollmentToken: vi.fn(),
  },
}));

vi.mock("../utils/qrSvg", () => ({
  enrollHref: (token: { path: string; url: string | null }) => token.url || token.path,
  qrSvg: vi.fn(async () => "<svg data-testid=\"qr-mark\"></svg>"),
}));

describe("EnrollmentQrModal", () => {
  beforeEach(() => {
    vi.mocked(api.createPromoEnrollmentToken).mockReset();
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    vi.setSystemTime(new Date("2026-09-03T12:00:00Z"));
    vi.mocked(api.createPromoEnrollmentToken).mockResolvedValue({
      path: "/acoes/participar/tok",
      url: "http://localhost/acoes/participar/tok",
      expires_at: "2026-09-03T12:10:00Z",
      expires_in_seconds: 600,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows a 10-minute countdown and expires with fake timers", async () => {
    render(<EnrollmentQrModal open actionId={1} onClose={() => undefined} />);

    expect(await screen.findByText("Validade: 10:00")).toBeInTheDocument();
    expect(screen.getByTestId("qr-mark")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(screen.getByText("Validade: 09:59")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(599_000);
    });
    expect(screen.getByText("Link expirado. Gere outro QR.")).toBeInTheDocument();
  });
});
