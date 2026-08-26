import type {

  CalcularResponse,

  Match,

  Player,

  Preset,

  PresetsResponse,

  Round,

  Standing,

  TabelaLinha,

  Torneio,

} from "./types";



const BASE = "/api/v1";

type ValidationErrorItem = {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
};

/** Formata detail do FastAPI (string ou lista Pydantic) para exibição na UI. */
export function formatApiError(detail: unknown, fallback = "Erro na requisição"): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          const err = item as ValidationErrorItem;
          const where = err.loc?.length
            ? err.loc.filter((p) => p !== "body").join(".") || "requisição"
            : "requisição";
          return where !== "requisição" ? `${where}: ${err.msg}` : (err.msg ?? fallback);
        }
        return null;
      })
      .filter(Boolean);
    if (parts.length) return parts.join("; ");
  }
  return fallback;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    ...init,
    credentials: "include",
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



export const api = {

  health: () => request<{ status: string }>("/health"),

  authStatus: () =>
    request<{ configured: boolean; min_password_length: number }>("/auth/status"),

  authMe: () =>
    request<{
      id: number;
      email: string;
      display_name: string;
      role: string;
      status: string;
    }>("/auth/me"),

  login: (email: string, password: string) =>
    request<{
      id: number;
      email: string;
      display_name: string;
      role: string;
    }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  register: (body: {
    display_name: string;
    email: string;
    phone: string;
    password: string;
    birth_date: string;
    guardian_name?: string;
    guardian_phone?: string;
    guardian_relation?: string;
  }) =>
    request<{
      id: number;
      email: string;
      display_name: string;
      role: string;
    }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" }),

  claimInvite: (body: {
    token: string;
    password: string;
    birth_date: string;
    guardian_name?: string;
    guardian_phone?: string;
    guardian_relation?: string;
  }) =>
    request<{ id: number; email: string; display_name: string }>("/auth/claim-invite", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listUsers: (q?: string) =>
    request<
      Array<{
        id: number;
        email: string;
        display_name: string;
        phone: string | null;
        role: string;
        status: string;
      }>
    >(`/users${q ? `?q=${encodeURIComponent(q)}` : ""}`),

  searchUsers: (q: string) =>
    request<
      Array<{
        id: number;
        display_name: string;
        email?: string;
        phone?: string | null;
        role: string;
        status: string;
      }>
    >(`/users/search?q=${encodeURIComponent(q)}`),

  createUser: (body: {
    display_name: string;
    email: string;
    phone: string;
    role?: string;
  }) =>
    request("/users", { method: "POST", body: JSON.stringify(body) }),

  inviteUser: (userId: number) =>
    request<{ token: string; claim_path: string; expires_at: string }>(`/users/${userId}/invite`, {
      method: "POST",
    }),

  ranking: () =>
    request<Array<{ rank: number; user_id: number; display_name: string; points: number }>>(
      "/ranking",
    ),

  publicProfile: (userId: number) => request(`/jogadores/${userId}/perfil`),

  checkInPlayer: (eventId: number, playerId: number) =>
    request(`/torneios/${eventId}/jogadores/${playerId}/check-in`, { method: "POST" }),

  selfRegister: (eventId: number) =>
    request(`/torneios/${eventId}/inscrever`, { method: "POST" }),

  createExternalTorneio: (body: unknown) =>
    request<Torneio>("/torneios/externos", { method: "POST", body: JSON.stringify(body) }),

  changePassword: (current_password: string, new_password: string) =>
    request<{ ok: boolean; message: string }>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password }),
    }),

  getPresets: () => request<PresetsResponse>("/premiacao/presets"),
  updatePreset: (id: string, body: Preset, expectedMtime?: number) =>

    request<Preset>(`/premiacao/presets/${id}`, {

      method: "PUT",

      headers: expectedMtime != null ? { "X-Presets-Mtime": String(expectedMtime) } : {},

      body: JSON.stringify(body),

    }),

  calcular: (
    jogadores: number,
    presetId?: string,
    valorInscricao?: number,
    formato?: "swiss" | "single_elimination",
    thirdPlaceMatch?: boolean,
  ) =>
    request<CalcularResponse>("/premiacao/calcular", {
      method: "POST",
      body: JSON.stringify({
        jogadores,
        preset_id: presetId,
        valor_inscricao: valorInscricao,
        formato: formato ?? "swiss",
        third_place_match: thirdPlaceMatch ?? false,
      }),
    }),

  tabela: (ate: number, presetId?: string) =>

    request<{ linhas: TabelaLinha[] }>(

      `/premiacao/tabela?ate=${ate}${presetId ? `&preset_id=${presetId}` : ""}`,

    ),

  exportCsv: async (ate: number, presetId?: string) => {

    const res = await fetch(`${BASE}/premiacao/export`, {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ ate, preset_id: presetId }),

    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err.detail, "Erro ao exportar"));
    }

    const blob = await res.blob();

    const disp = res.headers.get("Content-Disposition") || "";

    const match = disp.match(/filename="([^"]+)"/);

    const filename = match?.[1] ?? `premiacao_${ate}.csv`;

    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;

    a.download = filename;

    a.click();

    URL.revokeObjectURL(url);

  },



  listTorneios: () => request<Torneio[]>("/torneios"),

  getTorneio: (id: number) => request<Torneio & { players: Player[] }>(`/torneios/${id}`),

  createTorneio: (body: object) =>
    request<Torneio>("/torneios", { method: "POST", body: JSON.stringify(body) }),

  deleteTorneio: (id: number) =>
    request<void>(`/torneios/${id}`, { method: "DELETE" }),

  updateTorneio: (id: number, body: object) =>

    request<Torneio>(`/torneios/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  addJogador: (
    id: number,
    name: string,
    seed?: number,
    extra?: {
      email?: string;
      phone?: string;
      create_account?: boolean;
      user_id?: number;
    },
  ) =>
    request<Player>(`/torneios/${id}/jogadores`, {
      method: "POST",
      body: JSON.stringify({ name, seed, ...extra }),
    }),

  removeJogador: (id: number, pid: number) =>

    request<void>(`/torneios/${id}/jogadores/${pid}`, { method: "DELETE" }),

  iniciarTorneio: (id: number) =>

    request<Torneio>(`/torneios/${id}/iniciar`, { method: "POST" }),

  getRodadas: (id: number) => request<Round[]>(`/torneios/${id}/rodadas`),

  getRodada: (id: number, n: number) => request<Round>(`/torneios/${id}/rodadas/${n}`),

  updateMatch: (id: number, mid: number, score_p1: number, score_p2: number) =>

    request<Match>(`/torneios/${id}/matches/${mid}`, {

      method: "PATCH",

      body: JSON.stringify({ score_p1, score_p2 }),

    }),

  dropJogador: (id: number, pid: number, midRound: boolean) =>

    request<void>(`/torneios/${id}/jogadores/${pid}/drop`, {

      method: "POST",

      body: JSON.stringify({ mid_round: midRound }),

    }),

  completarRodada: (id: number) => request<Torneio>(`/torneios/${id}/avancar`, { method: "POST" }),

  iniciarProximaRodada: (id: number) =>

    request<Torneio>(`/torneios/${id}/iniciar-proxima-rodada`, { method: "POST" }),

  reabrirRodada: (id: number, number?: number) =>

    request<Torneio>(

      `/torneios/${id}/rodadas/reabrir${number != null ? `?number=${number}` : ""}`,

      { method: "POST" },

    ),

  finalizar: (id: number) => request<Torneio>(`/torneios/${id}/finalizar`, { method: "POST" }),

  getClassificacao: (id: number) =>

    request<{ standings: Standing[] }>(`/torneios/${id}/classificacao`),

  updateDecklists: (id: number, updates: { player_id: number; decklist: string | null }[]) =>

    request<void>(`/torneios/${id}/classificacao`, {

      method: "PATCH",

      body: JSON.stringify({ updates }),

    }),

  getPremiacao: (id: number) => request<object>(`/torneios/${id}/premiacao`),

  exportLog: async (id: number) => {

    const res = await fetch(`${BASE}/torneios/${id}/export-log`, { method: "POST" });

    if (!res.ok) {

      const err = await res.json().catch(() => ({ detail: "Erro ao exportar log" }));

      throw new Error(formatApiError(err.detail, "Erro ao exportar log"));

    }

    const blob = await res.blob();

    const disp = res.headers.get("Content-Disposition") || "";

    const match = disp.match(/filename="([^"]+)"/);

    const filename = match?.[1] ?? `torneio_${id}_log.json`;

    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;

    a.download = filename;

    a.click();

    URL.revokeObjectURL(url);

  },

};


