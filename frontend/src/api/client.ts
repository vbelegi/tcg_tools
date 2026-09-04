import type {
  CalcularResponse,
  Match,
  Player,
  PlayerDeck,
  PlayerProfile,
  Preset,
  PresetsResponse,
  PromoAction,
  PromoActionLog,
  PromoActionType,
  PromoDrawResult,
  PromoEnrollResult,
  PromoEnrollmentToken,
  PromoParticipant,
  Round,
  Standing,
  TabelaLinha,
  TcgGame,
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
  if (detail && typeof detail === "object" && "message" in detail) {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string" && message.trim()) return message;
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
      phone?: string | null;
      pending_phone?: string | null;
      birth_date?: string | null;
      avatar_url?: string | null;
      created_at?: string | null;
      email_verified?: boolean;
      email_verified_at?: string | null;
      phone_verified_at?: string | null;
      pending_email?: string | null;
      marketing_opt_out?: boolean;
      privacy_accepted_at?: string | null;
    }>("/auth/me"),

  updateMe: (body: {
    display_name?: string;
    phone?: string;
    birth_date?: string;
    guardian_name?: string | null;
    guardian_phone?: string | null;
    guardian_relation?: string | null;
    marketing_opt_out?: boolean;
  }) =>
    request<{
      id: number;
      email: string;
      display_name: string;
      role: string;
      status: string;
      phone?: string | null;
      avatar_url?: string | null;
      marketing_opt_out?: boolean;
      pending_email?: string | null;
      phone_verified_at?: string | null;
    }>("/auth/me", { method: "PATCH", body: JSON.stringify(body) }),

  requestEmailChange: (body: { current_password: string; new_email: string }) =>
    request<{
      ok: boolean;
      pending: boolean;
      message: string;
      user: {
        id: number;
        email: string;
        pending_email?: string | null;
        email_verified?: boolean;
      };
    }>("/auth/me/email-change", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  cancelEmailChange: () =>
    request<{ ok: boolean; user: { email: string; pending_email?: string | null } }>(
      "/auth/me/email-change/cancel",
      { method: "POST", body: JSON.stringify({}) },
    ),

  resendEmailChange: () =>
    request<{
      ok: boolean;
      pending: boolean;
      message: string;
      user: { email: string; pending_email?: string | null };
    }>("/auth/me/email-change/resend", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  confirmEmailChange: (token: string) =>
    request<{ email: string; email_verified: boolean; pending_email?: string | null }>(
      "/auth/email-change/confirm",
      { method: "POST", body: JSON.stringify({ token }) },
    ),

  cancelEmailChangeByToken: (token: string) =>
    request<{ ok: boolean; message: string }>("/auth/email-change/cancel", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),

  exportMe: () =>
    request<Record<string, unknown>>("/auth/me/export"),

  deleteMe: (body: { password: string; confirm: string }) =>
    request<{ ok: boolean }>("/auth/me/delete", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  uploadAvatar: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/auth/me/avatar`, {
      method: "POST",
      credentials: "include",
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err.detail, res.statusText || "Erro no upload"));
    }
    return res.json() as Promise<{
      id: number;
      display_name: string;
      avatar_url?: string | null;
    }>;
  },

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
    accept_privacy: boolean;
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
    accept_privacy: boolean;
  }) =>
    request<{ id: number; email: string; display_name: string }>("/auth/claim-invite", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  claimPasswordReset: (token: string, password: string) =>
    request<{ id: number; email: string; display_name: string }>("/auth/claim-password-reset", {
      method: "POST",
      body: JSON.stringify({ token, password }),
    }),

  verifyEmail: (token: string) =>
    request<{ email_verified: boolean }>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),

  resendVerification: () =>
    request<{ ok: boolean; message: string }>("/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  forgotPassword: (email: string) =>
    request<{ ok: boolean; message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
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

  exportContactsCsv: async () => {
    const res = await fetch(`${BASE}/users/export-contacts`, { credentials: "include" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err.detail, res.statusText || "Erro no export"));
    }
    const blob = await res.blob();
    const dispo = res.headers.get("Content-Disposition") || "";
    const match = /filename="?([^"]+)"?/.exec(dispo);
    const filename = match?.[1] || "fourse-contatos.csv";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },

  deleteUser: (userId: number) =>
    request<{ ok: boolean }>(`/users/${userId}/delete`, { method: "POST" }),

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

  searchPlayers: (q: string) =>
    request<Array<{ id: number; display_name: string; avatar_url: string | null }>>(
      `/jogadores/buscar?q=${encodeURIComponent(q)}`,
    ),

  createUser: (body: {
    display_name: string;
    email: string;
    phone: string;
    role?: string;
  }) =>
    request("/users", { method: "POST", body: JSON.stringify(body) }),

  inviteUser: (userId: number) =>
    request<{ token: string; claim_path: string; claim_url: string | null; expires_at: string }>(
      `/users/${userId}/invite`,
      { method: "POST" },
    ),

  resetUserPassword: (userId: number) =>
    request<{ reset_path: string; reset_url: string | null; expires_at: string }>(
      `/users/${userId}/password-reset`,
      { method: "POST" },
    ),

  updateUserRole: (userId: number, role: string, current_password: string) =>
    request<{ id: number; role: string }>(`/users/${userId}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role, current_password }),
    }),

  listAuditLogs: (opts?: {
    action?: string;
    actor_user_id?: number;
    target_user_id?: number;
    from?: string;
    to?: string;
    limit?: number;
    offset?: number;
  }) => {
    const params = new URLSearchParams();
    if (opts?.action) params.set("action", opts.action);
    if (opts?.actor_user_id != null) params.set("actor_user_id", String(opts.actor_user_id));
    if (opts?.target_user_id != null) params.set("target_user_id", String(opts.target_user_id));
    if (opts?.from) params.set("from", opts.from);
    if (opts?.to) params.set("to", opts.to);
    if (opts?.limit != null) params.set("limit", String(opts.limit));
    if (opts?.offset != null) params.set("offset", String(opts.offset));
    const qs = params.toString();
    return request<{
      total: number;
      limit: number;
      offset: number;
      items: Array<{
        id: number;
        action: string;
        actor_user_id: number | null;
        actor_display_name: string | null;
        target_user_id: number | null;
        target_display_name: string | null;
        meta: Record<string, unknown> | null;
        ip: string | null;
        created_at: string | null;
      }>;
    }>(`/audit-logs${qs ? `?${qs}` : ""}`);
  },

  ranking: () =>
    request<
      Array<{
        rank: number;
        user_id: number;
        display_name: string;
        points: number;
        avatar_url: string | null;
      }>
    >("/ranking"),

  publicProfile: (userId: number) => request<PlayerProfile>(`/jogadores/${userId}/perfil`),

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
      credentials: "include",
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



  listTorneios: (opts?: {
    q?: string;
    active?: boolean;
    from?: string;
    to?: string;
  }) => {
    const params = new URLSearchParams();
    if (opts?.q) params.set("q", opts.q);
    if (opts?.active) params.set("active", "true");
    if (opts?.from) params.set("from", opts.from);
    if (opts?.to) params.set("to", opts.to);
    const qs = params.toString();
    return request<Torneio[]>(`/torneios${qs ? `?${qs}` : ""}`);
  },

  listCalendarTorneios: (year: number, month: number) =>
    request<Torneio[]>(`/torneios/calendar?year=${year}&month=${month}`),

  getCalendar: (year: number, month: number) =>
    request<{
      tournaments: Torneio[];
      announcements: Array<{
        id: number;
        title: string;
        event_date: string;
        description: string | null;
        start_time: string | null;
        location: string | null;
      }>;
      promo_actions: Array<{
        id: number;
        name: string;
        start_date: string;
        end_date: string;
        description: string | null;
        type_label: string;
      }>;
    }>(`/calendar?year=${year}&month=${month}`),

  listCalendarAnnouncements: (opts?: {
    year?: number;
    month?: number;
    q?: string;
    from?: string;
    to?: string;
  }) => {
    const params = new URLSearchParams();
    if (opts?.year != null) params.set("year", String(opts.year));
    if (opts?.month != null) params.set("month", String(opts.month));
    if (opts?.q) params.set("q", opts.q);
    if (opts?.from) params.set("from", opts.from);
    if (opts?.to) params.set("to", opts.to);
    const qs = params.toString();
    return request<
      Array<{
        id: number;
        title: string;
        event_date: string;
        description: string | null;
        start_time: string | null;
        location: string | null;
      }>
    >(`/calendar/announcements${qs ? `?${qs}` : ""}`);
  },

  createCalendarAnnouncement: (body: {
    title: string;
    event_date: string;
    description?: string | null;
    start_time?: string | null;
    location?: string | null;
  }) =>
    request("/calendar/announcements", { method: "POST", body: JSON.stringify(body) }),

  updateCalendarAnnouncement: (
    id: number,
    body: {
      title?: string;
      event_date?: string;
      description?: string | null;
      start_time?: string | null;
      location?: string | null;
    },
  ) =>
    request(`/calendar/announcements/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  deleteCalendarAnnouncement: (id: number) =>
    request<void>(`/calendar/announcements/${id}`, { method: "DELETE" }),

  listTcgGames: (includeInactive = false) =>
    request<TcgGame[]>(`/tcg-games${includeInactive ? "?include_inactive=true" : ""}`),

  createTcgGame: (body: { name: string; color_hex: string; slug?: string; active?: boolean }) =>
    request<TcgGame>("/tcg-games", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateTcgGame: (
    id: number,
    body: { name?: string; color_hex?: string; slug?: string; active?: boolean },
  ) =>
    request<TcgGame>(`/tcg-games/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  deleteTcgGame: (id: number) => request<void>(`/tcg-games/${id}`, { method: "DELETE" }),

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

  finalizarColocacoes: (id: number, body: object) =>
    request<Torneio>(`/torneios/${id}/finalizar-colocacoes`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

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

  getPlayerDeck: (eventId: number, playerId: number) =>
    request<PlayerDeck>(`/torneios/${eventId}/jogadores/${playerId}/deck`),

  updateDecklists: (
    id: number,
    updates: {
      player_id: number;
      decklist: string | null;
      decklist_source?: string | null;
      decklist_source_id?: string | null;
      decklist_source_url?: string | null;
      decklist_name?: string | null;
      decklist_format?: string | null;
      decklist_price_low_brl?: number | null;
    }[],
  ) =>
    request<void>(`/torneios/${id}/classificacao`, {
      method: "PATCH",
      body: JSON.stringify({ updates }),
    }),

  previewDeckImport: (url: string) =>
    request<{
      source: string;
      source_deck_id: string;
      source_url: string;
      name: string | null;
      format: string | null;
      plain_text: string;
      card_count: number;
      price_low_brl: number | null;
      price_currency: string;
      warnings: string[];
    }>("/decks/import/preview", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),

  getPremiacao: (id: number) => request<object>(`/torneios/${id}/premiacao`),

  exportLog: async (id: number) => {
    const res = await fetch(`${BASE}/torneios/${id}/export`, {
      method: "GET",
      credentials: "include",
    });

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

  listPromoActions: (params?: { q?: string; active?: boolean }) => {
    const search = new URLSearchParams();
    if (params?.q) search.set("q", params.q);
    if (params?.active) search.set("active", "true");
    const qs = search.toString();
    return request<PromoAction[]>(`/acoes${qs ? `?${qs}` : ""}`);
  },

  getPromoAction: (id: number) => request<PromoAction>(`/acoes/${id}`),

  listPromoActionTypes: () => request<PromoActionType[]>("/acoes/tipos"),

  createPromoAction: (body: {
    name: string;
    type: string;
    start_date: string;
    end_date: string;
    description?: string | null;
    published?: boolean;
    show_in_calendar?: boolean;
    max_participants?: number | null;
  }) => request<PromoAction>("/acoes", { method: "POST", body: JSON.stringify(body) }),

  updatePromoAction: (
    id: number,
    body: {
      name?: string;
      start_date?: string;
      end_date?: string;
      description?: string | null;
      show_in_calendar?: boolean;
      max_participants?: number | null;
    },
  ) => request<PromoAction>(`/acoes/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  publishPromoAction: (id: number) =>
    request<PromoAction>(`/acoes/${id}/publish`, { method: "POST" }),

  /** XHR instead of fetch so the PDF upload can report progress. */
  uploadPromoRegulation: (
    id: number,
    file: File,
    onProgress?: (percent: number) => void,
  ) =>
    new Promise<PromoAction>((resolve, reject) => {
      const form = new FormData();
      form.append("file", file);
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${BASE}/acoes/${id}/regulamento`);
      xhr.withCredentials = true;
      xhr.upload.onprogress = (event) => {
        if (onProgress && event.lengthComputable) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      };
      xhr.onload = () => {
        let body: { detail?: unknown } = {};
        try {
          body = JSON.parse(xhr.responseText);
        } catch {
          body = {};
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(body as unknown as PromoAction);
        } else {
          reject(new Error(formatApiError(body.detail, "Erro no upload do regulamento")));
        }
      };
      xhr.onerror = () => reject(new Error("Erro de rede no upload do regulamento."));
      xhr.send(form);
    }),

  createPromoEnrollmentToken: (id: number) =>
    request<PromoEnrollmentToken>(`/acoes/${id}/enrollment-token`, { method: "POST" }),

  /** Always returns a named `reason`; does not throw on 4xx with a reason body. */
  enrollPromo: (token: string) => enrollRequest(`/acoes/enroll/${encodeURIComponent(token)}`),

  completePromoEnroll: () =>
    enrollRequest("/acoes/enroll/complete", { method: "POST" }),

  listPromoParticipants: (id: number) =>
    request<PromoParticipant[]>(`/acoes/${id}/participants`),

  listPromoLogs: (id: number) => request<PromoActionLog[]>(`/acoes/${id}/logs`),

  drawPromoAction: (
    id: number,
    body: { mode: "direct" | "chained"; winner_count?: number; winner_user_ids?: number[] },
  ) => request<PromoDrawResult>(`/acoes/${id}/draw`, { method: "POST", body: JSON.stringify(body) }),

  listPromoWinners: (id: number) => request<PromoDrawResult>(`/acoes/${id}/winners`),

  exportPromoWinnersCsv: async (id: number) => {
    const res = await fetch(`${BASE}/acoes/${id}/winners.csv`, { credentials: "include" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err.detail, res.statusText || "Erro no export"));
    }
    const blob = await res.blob();
    const dispo = res.headers.get("Content-Disposition") || "";
    const match = /filename="?([^"]+)"?/.exec(dispo);
    const filename = match?.[1] || `acao-${id}-sorteados.csv`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },

};

async function enrollRequest(url: string, init?: RequestInit): Promise<PromoEnrollResult> {
  const res = await fetch(`${BASE}${url}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  const body = (await res.json().catch(() => ({}))) as PromoEnrollResult & { detail?: unknown };
  if (body && typeof body.reason === "string") {
    return body;
  }
  if (body && body.detail && typeof body.detail === "object" && body.detail !== null && "reason" in body.detail) {
    const nested = body.detail as PromoEnrollResult;
    if (nested.reason) return nested;
  }
  throw new Error(formatApiError(body.detail, res.statusText || "Erro na inscrição"));
}


