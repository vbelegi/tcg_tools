import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "../api/client";
import type { ProfileHistoryRow } from "../api/types";
import { ChangePasswordModal } from "../components/ChangePasswordModal";
import { Switch } from "../components/Switch";
import { resolveAvatarUrl, tcgIconUrl } from "../utils/tcgIcons";

function formatFinish(rank: number | null | undefined): string {
  if (rank == null) return "—";
  return `${rank}º`;
}

function historyVisible(rows: ProfileHistoryRow[], filter: string, limit: number) {
  const filtered =
    filter === "all"
      ? rows
      : rows.filter((h) => (h.tcg_game?.name ?? "Outros") === filter);
  return { total: filtered.length, rows: filtered.slice(0, limit) };
}

export function PlayerProfilePage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const userId = Number(id);
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [nameDraft, setNameDraft] = useState("");
  const [editingName, setEditingName] = useState(false);
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [historyFilter, setHistoryFilter] = useState("all");
  const [historyLimit, setHistoryLimit] = useState(8);
  const [error, setError] = useState("");
  const [searchQ, setSearchQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [showDelete, setShowDelete] = useState(false);

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedQ(searchQ.trim()), 250);
    return () => window.clearTimeout(t);
  }, [searchQ]);

  const { data, isLoading, error: loadError } = useQuery({
    queryKey: ["profile", userId],
    queryFn: () => api.publicProfile(userId),
    enabled: Number.isFinite(userId),
  });

  const { data: me } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });

  const { data: searchHits = [], isFetching: searching } = useQuery({
    queryKey: ["player-search", debouncedQ],
    queryFn: () => api.searchPlayers(debouncedQ),
    enabled: debouncedQ.length >= 2,
  });

  const saveName = useMutation({
    mutationFn: () => api.updateMe({ display_name: nameDraft }),
    onSuccess: async () => {
      setEditingName(false);
      await qc.invalidateQueries({ queryKey: ["profile", userId] });
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const uploadAvatar = useMutation({
    mutationFn: (file: File) => api.uploadAvatar(file),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["profile", userId] });
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const marketingToggle = useMutation({
    mutationFn: (optOut: boolean) => api.updateMe({ marketing_opt_out: optOut }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const exportMyData = useMutation({
    mutationFn: async () => {
      const data = await api.exportMe();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `meus-dados-fourse.json`;
      a.click();
      URL.revokeObjectURL(url);
    },
    onError: (e) => setError((e as Error).message),
  });

  const deleteAccount = useMutation({
    mutationFn: () =>
      api.deleteMe({ password: deletePassword, confirm: deleteConfirm }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
      navigate("/", { replace: true });
    },
    onError: (e) => setError((e as Error).message),
  });

  const filters = useMemo(() => {
    if (!data) return ["all"];
    const names = new Set<string>();
    for (const h of data.history) {
      names.add(h.tcg_game?.name ?? "Outros");
    }
    return ["all", ...Array.from(names).sort()];
  }, [data]);

  const chartGames = useMemo(
    () =>
      (data?.fp_by_game ?? []).map((g) => ({
        name: g.tcg_name.length > 10 ? g.tcg_name.slice(0, 9) + "…" : g.tcg_name,
        full: g.tcg_name,
        points: g.points,
      })),
    [data],
  );

  const chartMonths = useMemo(
    () =>
      (data?.fp_by_month ?? []).map((m) => ({
        month: m.month.slice(5) + "/" + m.month.slice(2, 4),
        points: m.points,
      })),
    [data],
  );

  if (isLoading) return <p>Carregando...</p>;
  if (loadError) return <p className="error">{(loadError as Error).message}</p>;
  if (!data) return null;

  const canEdit = Boolean(data.can_edit || (me && me.id === data.id));
  const showFp = data.fourse_points_visible && data.fourse_points != null;
  const sinceYear = data.created_at ? new Date(data.created_at).getFullYear() : null;
  const { total: histTotal, rows: histRows } = historyVisible(
    data.history,
    historyFilter,
    historyLimit,
  );
  const mainGame = (() => {
    if (data.fp_by_game[0]?.tcg_name) return data.fp_by_game[0].tcg_name;
    const counts = new Map<string, number>();
    for (const h of data.history) {
      const name = h.tcg_game?.name;
      if (!name) continue;
      counts.set(name, (counts.get(name) ?? 0) + 1);
    }
    let bestName: string | null = null;
    let bestCount = 0;
    for (const [name, n] of counts) {
      if (n > bestCount) {
        bestName = name;
        bestCount = n;
      }
    }
    return bestName ?? data.badge_games[0]?.name ?? "—";
  })();

  const onSaveName = (e: FormEvent) => {
    e.preventDefault();
    saveName.mutate();
  };

  return (
    <div className="profile-page">
      <div className="profile-toolbar">
        <div className="profile-search">
          <label htmlFor="profile-player-search" className="sr-only">
            Buscar jogador
          </label>
          <input
            id="profile-player-search"
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
            placeholder="Buscar jogador…"
            autoComplete="off"
          />
          {debouncedQ.length >= 2 && (
            <ul className="profile-search-results">
              {searching && <li className="muted">Buscando…</li>}
              {!searching && searchHits.length === 0 && (
                <li className="muted">Nenhum jogador encontrado.</li>
              )}
              {searchHits.map((hit) => (
                <li key={hit.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQ("");
                      setDebouncedQ("");
                      navigate(`/jogadores/${hit.id}`);
                    }}
                  >
                    <img
                      src={resolveAvatarUrl(hit.avatar_url)}
                      alt=""
                      width={28}
                      height={28}
                    />
                    <span>{hit.display_name}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <section className="profile-hero">
        <div className="profile-hero-main">
          <div className="profile-avatar-wrap">
            <img
              className="profile-avatar"
              src={resolveAvatarUrl(data.avatar_url)}
              alt=""
              width={96}
              height={96}
            />
            {canEdit && (
              <>
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  hidden
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setError("");
                      uploadAvatar.mutate(file);
                    }
                    e.target.value = "";
                  }}
                />
                <button
                  type="button"
                  className="secondary profile-avatar-btn"
                  onClick={() => fileRef.current?.click()}
                  disabled={uploadAvatar.isPending}
                >
                  Trocar foto
                </button>
              </>
            )}
          </div>
          <div className="profile-hero-text">
            {editingName && canEdit ? (
              <form className="profile-name-form" onSubmit={onSaveName}>
                <input
                  value={nameDraft}
                  onChange={(e) => setNameDraft(e.target.value)}
                  maxLength={120}
                  required
                />
                <button type="submit" className="primary" disabled={saveName.isPending}>
                  Salvar
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setEditingName(false)}
                >
                  Cancelar
                </button>
              </form>
            ) : (
              <div className="profile-name-row">
                <h1>{data.display_name}</h1>
                {canEdit && (
                  <>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => {
                        setNameDraft(data.display_name);
                        setEditingName(true);
                      }}
                    >
                      Editar nome
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => setPasswordOpen(true)}
                    >
                      Alterar senha
                    </button>
                  </>
                )}
              </div>
            )}
            <div className="profile-badges-row">
              {data.status === "incomplete" && (
                <span className="profile-pill muted">Cadastro incompleto</span>
              )}
              {data.ranking_position != null && (
                <span className="profile-pill">#{data.ranking_position} no Ranking</span>
              )}
              {sinceYear != null && (
                <span className="profile-pill muted">Desde {sinceYear}</span>
              )}
              {data.badge_games.map((g) => (
                <img
                  key={g.id}
                  className="profile-tcg-badge"
                  src={tcgIconUrl(g.name)}
                  alt={g.name}
                  title={g.name}
                  width={36}
                  height={36}
                  onError={(e) => {
                    (e.currentTarget as HTMLImageElement).src = "/tcg-icons/other.png";
                  }}
                />
              ))}
            </div>
          </div>
        </div>
        {showFp && (
          <div className="profile-fp-card">
            <span className="profile-fp-label">Fourse Points</span>
            <strong className="profile-fp-value">{data.fourse_points}</strong>
          </div>
        )}
      </section>

      <section className="profile-stats">
        <div className="profile-stat">
          <span>Torneios</span>
          <strong>{data.stats.tournaments}</strong>
        </div>
        <div className="profile-stat">
          <span>Títulos</span>
          <strong className="accent-gold">{data.stats.titles}</strong>
        </div>
        <div className="profile-stat">
          <span>Top 8</span>
          <strong className="accent-blue">{data.stats.top8}</strong>
        </div>
        <div className="profile-stat">
          <span>Melhor colocação</span>
          <strong className="accent-green">{formatFinish(data.stats.best_finish)}</strong>
        </div>
      </section>

      {data.insights.length > 0 && (
        <section className="profile-section">
          <h2>Insights</h2>
          <div className="profile-insights">
            {data.insights.map((text) => (
              <article key={text} className="profile-insight">
                {text}
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="profile-section">
        <h2>Perfil resumido</h2>
        <div className="profile-summary-grid">
          <article className="profile-summary-card">
            <span>Jogo principal</span>
            <strong>{mainGame}</strong>
          </article>
          <article className="profile-summary-card">
            <span>Melhor colocação</span>
            <strong>{formatFinish(data.stats.best_finish)} lugar</strong>
          </article>
          <article className="profile-summary-card">
            <span>Torneios finalizados</span>
            <strong>{data.stats.tournaments}</strong>
          </article>
        </div>
      </section>

      {showFp && (
        <div className="profile-charts">
          <section className="profile-section profile-chart-card">
            <h2>Pontos por jogo</h2>
            {chartGames.length === 0 ? (
              <p className="muted">Sem dados ainda.</p>
            ) : (
              <div className="profile-chart">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={chartGames}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#3a2a4a" />
                    <XAxis dataKey="name" stroke="#a898b8" fontSize={12} />
                    <YAxis stroke="#a898b8" fontSize={12} />
                    <Tooltip
                      contentStyle={{ background: "#1c1028", border: "1px solid #3a2a4a" }}
                      labelFormatter={(_, payload) =>
                        (payload?.[0]?.payload as { full?: string } | undefined)?.full ?? ""
                      }
                    />
                    <Bar dataKey="points" fill="#9b2de0" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </section>

          <section className="profile-section profile-chart-card">
            <h2>Desempenho por temporada</h2>
            {chartMonths.length === 0 ? (
              <p className="muted">Sem dados ainda.</p>
            ) : (
              <div className="profile-chart">
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={chartMonths}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#3a2a4a" />
                    <XAxis dataKey="month" stroke="#a898b8" fontSize={12} />
                    <YAxis stroke="#a898b8" fontSize={12} />
                    <Tooltip
                      contentStyle={{ background: "#1c1028", border: "1px solid #3a2a4a" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="points"
                      stroke="#9b2de0"
                      strokeWidth={2}
                      dot={{ r: 4, fill: "#9b2de0" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </section>
        </div>
      )}

      <section className="profile-section">
        <div className="profile-history-head">
          <h2>Histórico completo de torneios</h2>
          <div className="profile-filters">
            {filters.map((f) => (
              <button
                key={f}
                type="button"
                className={historyFilter === f ? "primary" : "secondary"}
                onClick={() => {
                  setHistoryFilter(f);
                  setHistoryLimit(8);
                }}
              >
                {f === "all" ? "Todos" : f}
              </button>
            ))}
          </div>
        </div>
        {histTotal === 0 ? (
          <p className="muted">Nenhum torneio finalizado vinculado.</p>
        ) : (
          <>
            <div className="table-wrap">
              <table className="profile-history-table">
                <thead>
                  <tr>
                    <th>Data</th>
                    <th>Torneio</th>
                    <th>Jogo</th>
                    <th>Colocação</th>
                    <th>Participantes</th>
                  </tr>
                </thead>
                <tbody>
                  {histRows.map((h) => (
                    <tr key={`${h.event_id}-${h.rank_label}`}>
                      <td>{h.event_date.split("-").reverse().join("/")}</td>
                      <td>
                        <Link to={`/torneios/${h.event_id}/resultado`}>{h.event_name}</Link>
                      </td>
                      <td
                        style={{
                          color: h.tcg_game?.color_hex ?? "var(--muted)",
                          fontWeight: 600,
                        }}
                      >
                        {h.tcg_game?.name ?? "—"}
                      </td>
                      <td>
                        {h.is_drop ? (
                          "DROP"
                        ) : h.rank != null && h.rank <= 8 ? (
                          <span className="profile-place-badge">{formatFinish(h.rank)}</span>
                        ) : (
                          formatFinish(h.rank)
                        )}
                      </td>
                      <td>{h.player_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {histTotal > historyLimit && (
              <button
                type="button"
                className="secondary"
                style={{ display: "block", margin: "1rem auto 0" }}
                onClick={() => setHistoryLimit((n) => n + 12)}
              >
                Ver todos ({histTotal})
              </button>
            )}
            {histRows.some((h) => h.decklist) && (
              <div className="profile-decklists">
                <h3>Decklists</h3>
                {histRows
                  .filter((h) => h.decklist)
                  .map((h) => (
                    <details key={`deck-${h.event_id}`}>
                      <summary>
                        {h.event_name} ({h.event_date})
                      </summary>
                      <pre>{h.decklist}</pre>
                    </details>
                  ))}
              </div>
            )}
          </>
        )}
      </section>

      {canEdit && me && me.id === data.id && (
        <section className="profile-privacy-section resultado-section">
          <h2>Conta e comunicações</h2>
          <p className="field-hint">
            Preferências discretas de contato e direitos sobre seus dados.{" "}
            <Link to="/privacidade">Política de privacidade</Link>
          </p>
          <Switch
            className="auth-privacy-check"
            checked={!Boolean(me.marketing_opt_out)}
            onChange={(checked) => marketingToggle.mutate(!checked)}
            disabled={marketingToggle.isPending}
          >
            Receber novidades e avisos da loja por WhatsApp/e-mail
          </Switch>
          <div className="profile-privacy-actions">
            <button
              type="button"
              className="secondary"
              onClick={() => exportMyData.mutate()}
              disabled={exportMyData.isPending}
            >
              Baixar meus dados
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => setShowDelete((v) => !v)}
            >
              Excluir minha conta
            </button>
          </div>
          {showDelete && (
            <form
              className="admin-form-dense"
              onSubmit={(e) => {
                e.preventDefault();
                deleteAccount.mutate();
              }}
            >
              <p className="field-hint">
                Histórico de torneios permanecerá como &quot;Anônimo&quot;. Digite sua senha e confirme com
                EXCLUIR.
              </p>
              <div className="form-row">
                <label>Senha</label>
                <input
                  type="password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <label>Confirmação</label>
                <input
                  value={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.value)}
                  placeholder="EXCLUIR"
                  required
                />
              </div>
              <button className="primary" type="submit" disabled={deleteAccount.isPending}>
                {deleteAccount.isPending ? "Excluindo…" : "Confirmar exclusão"}
              </button>
            </form>
          )}
        </section>
      )}

      <ChangePasswordModal open={passwordOpen} onClose={() => setPasswordOpen(false)} />
    </div>
  );
}
