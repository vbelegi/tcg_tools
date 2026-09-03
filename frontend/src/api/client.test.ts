import { describe, expect, it, vi, beforeEach } from "vitest";

import { api, formatApiError } from "./client";

const BASE = "/api/v1";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(formatApiError(err.detail, res.statusText || "Erro na requisição"));
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res as unknown as T;
}

describe("formatApiError", () => {
  it("returns string detail as-is", () => {
    expect(formatApiError("Rodada ativa")).toBe("Rodada ativa");
  });

  it("formats pydantic validation list", () => {
    const detail = [
      {
        type: "model_attributes_type",
        loc: ["body"],
        msg: "Input should be a valid dictionary or object to extract fields from",
      },
    ];
    expect(formatApiError(detail)).toContain("valid dictionary");
  });
});

describe("api request helper", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("returns JSON on success", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const data = await request<{ status: string }>("/health");
    expect(data.status).toBe("ok");
    expect(fetch).toHaveBeenCalledWith("/api/v1/health", expect.any(Object));
  });

  it("preserves Content-Type when custom headers are passed", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ label: "X" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await request("/premiacao/presets/standard", {
      method: "PUT",
      headers: { "X-Presets-Mtime": "1234567890" },
      body: JSON.stringify({ label: "X" }),
    });
    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/premiacao/presets/standard",
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          "X-Presets-Mtime": "1234567890",
        }),
      }),
    );
  });

  it("throws with API detail message on error", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Rodada ativa" }), {
        status: 422,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await expect(request("/torneios/1/finalizar", { method: "POST" })).rejects.toThrow(
      "Rodada ativa",
    );
  });

  it("handles 204 no content", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(null, { status: 204 }));
    const result = await request<void>("/torneios/1/jogadores/2", { method: "DELETE" });
    expect(result).toBeUndefined();
  });
});

describe("reabrirRodada URL", () => {
  it("builds optional round number query", () => {
    const id = 5;
    const withNumber = `/torneios/${id}/rodadas/reabrir?number=2`;
    const without = `/torneios/${id}/rodadas/reabrir`;
    expect(withNumber).toContain("number=2");
    expect(without).not.toContain("?");
  });
});

describe("api.enrollPromo", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("returns a named 409 reason without throwing", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          reason: "already_enrolled",
          message: "Você já está inscrito nesta ação.",
          action_id: 1,
          action_name: "Pré-venda",
          participation_status: "confirmed",
        }),
        { status: 409, headers: { "Content-Type": "application/json" } },
      ),
    );
    const body = await api.enrollPromo("tok");
    expect(body.reason).toBe("already_enrolled");
    expect(body.message).toContain("já está inscrito");
  });
});
