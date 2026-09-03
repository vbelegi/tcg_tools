import { describe, expect, it } from "vitest";

import { formatCountdown, formatDate, formatDateTime, formatPeriod, phaseLabel, promoPhase, todayIso } from "./promoFormat";

describe("promoFormat", () => {
  it("formats ISO dates as pt-BR", () => {
    expect(formatDate("2026-09-03")).toBe("03/09/2026");
    expect(formatPeriod("2026-09-01", "2026-09-15")).toBe("01/09/2026 a 15/09/2026");
  });

  it("derives today without timezone drift", () => {
    expect(todayIso(new Date(2026, 0, 5))).toBe("2026-01-05");
    expect(todayIso(new Date(2026, 11, 31))).toBe("2026-12-31");
  });

  it("classifies the action period", () => {
    const action = { start_date: "2026-09-01", end_date: "2026-09-15" };
    expect(promoPhase(action, "2026-08-31")).toBe("scheduled");
    expect(promoPhase(action, "2026-09-01")).toBe("running");
    expect(promoPhase(action, "2026-09-15")).toBe("running");
    expect(promoPhase(action, "2026-09-16")).toBe("ended");
  });

  it("labels each phase in pt-BR", () => {
    expect(phaseLabel("scheduled")).toBe("em breve");
    expect(phaseLabel("running")).toBe("em andamento");
    expect(phaseLabel("ended")).toBe("encerrada");
  });

  it("formats a countdown and UTC timestamps", () => {
    expect(formatCountdown(600)).toBe("10:00");
    expect(formatCountdown(59)).toBe("00:59");
    expect(formatCountdown(0)).toBe("00:00");
    expect(formatDateTime("2026-09-03T12:04:00Z")).toBe("03/09/2026 12:04");
  });
});
