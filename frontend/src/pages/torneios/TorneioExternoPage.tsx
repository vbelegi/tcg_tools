import { useEffect, useMemo, useState, type KeyboardEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { Switch } from "../../components/Switch";

type UserHit = {
  id: number;
  display_name: string;
  email?: string;
  phone?: string | null;
};

type PlacementRow = {
  key: string;
  placement: number;
  display_name: string;
  user_id: number | null;
  email: string;
  phone: string;
  create_account: boolean;
  decklist: string;
  is_drop: boolean;
  showDecklist: boolean;
  showIncomplete: boolean;
};

let rowKeySeq = 0;
function nextKey() {
  rowKeySeq += 1;
  return `ext-${rowKeySeq}`;
}

function emptyRow(placement: number): PlacementRow {
  return {
    key: nextKey(),
    placement,
    display_name: "",
    user_id: null,
    email: "",
    phone: "",
    create_account: false,
    decklist: "",
    is_drop: false,
    showDecklist: false,
    showIncomplete: false,
  };
}

function renumber(rows: PlacementRow[]): PlacementRow[] {
  return rows.map((r, i) => ({ ...r, placement: i + 1 }));
}

export function TorneioExternoPage() {
  const navigate = useNavigate();
  const { data: presets } = useQuery({ queryKey: ["presets"], queryFn: api.getPresets });
  const { data: tcgGames } = useQuery({
    queryKey: ["tcg-games"],
    queryFn: () => api.listTcgGames(),
  });

  const [name, setName] = useState("");
  const [eventDate, setEventDate] = useState(new Date().toISOString().slice(0, 10));
  const [entryFee, setEntryFee] = useState("0");
  const [presetId, setPresetId] = useState("standard");
  const [format, setFormat] = useState<"swiss" | "single_elimination">("swiss");
  const [tcgGameId, setTcgGameId] = useState("");
  const [notes, setNotes] = useState("");
  const [rows, setRows] = useState<PlacementRow[]>(() =>
    renumber([emptyRow(1), emptyRow(2), emptyRow(3), emptyRow(4)]),
  );
  const [error, setError] = useState("");
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [debouncedQ, setDebouncedQ] = useState("");
  const [hits, setHits] = useState<UserHit[]>([]);
  const [searchDone, setSearchDone] = useState(false);

  const activeRow = rows.find((r) => r.key === activeKey) ?? null;
  const searchQ = activeRow && !activeRow.user_id ? activeRow.display_name.trim() : "";

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedQ(searchQ), 280);
    return () => window.clearTimeout(t);
  }, [searchQ]);

  useEffect(() => {
    if (debouncedQ.length < 2 || !activeKey) {
      setHits([]);
      setSearchDone(false);
      return;
    }
    let cancelled = false;
    setSearchDone(false);
    api
      .searchUsers(debouncedQ)
      .then((data) => {
        if (!cancelled) {
          setHits(data);
          setSearchDone(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setHits([]);
          setSearchDone(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedQ, activeKey]);

  const updateRow = (key: string, patch: Partial<PlacementRow>) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  };

  const linkUser = (key: string, u: UserHit) => {
    updateRow(key, {
      user_id: u.id,
      display_name: u.display_name,
      email: "",
      phone: "",
      create_account: false,
      showIncomplete: false,
    });
    setActiveKey(null);
    setHits([]);
  };

  const clearLink = (key: string) => {
    updateRow(key, {
      user_id: null,
      display_name: "",
      create_account: false,
      showIncomplete: false,
      email: "",
      phone: "",
    });
  };

  const removeRow = (key: string) => {
    setRows((prev) => {
      if (prev.length <= 1) return prev;
      return renumber(prev.filter((r) => r.key !== key));
    });
    if (activeKey === key) setActiveKey(null);
  };

  const addRow = () => {
    setRows((prev) => renumber([...prev, emptyRow(prev.length + 1)]));
  };

  const filled = rows.filter((r) => r.display_name.trim() || r.user_id);
  const summary = useMemo(() => {
    const withAccount = filled.filter((r) => r.user_id || r.create_account).length;
    const nameOnly = filled.filter((r) => !r.user_id && !r.create_account).length;
    const drops = filled.filter((r) => r.is_drop).length;
    return { total: filled.length, withAccount, nameOnly, drops };
  }, [filled]);

  const mutation = useMutation({
    mutationFn: () => {
      if (!tcgGameId) throw new Error("Selecione o TCG do torneio.");
      const placements = rows
        .filter((r) => r.display_name.trim() || r.user_id)
        .map((r) => {
          if (r.create_account) {
            if (!r.email.trim() || !r.phone.trim()) {
              throw new Error(`Colocação ${r.placement}: incomplete exige e-mail e celular.`);
            }
          }
          return {
            placement: r.placement,
            display_name: r.display_name.trim() || "Jogador",
            user_id: r.user_id ?? undefined,
            email: r.create_account ? r.email.trim() : undefined,
            phone: r.create_account ? r.phone.trim() : undefined,
            create_account: r.create_account,
            decklist: r.decklist.trim() || undefined,
            is_drop: r.is_drop,
          };
        });
      if (placements.length < 1) throw new Error("Informe ao menos uma colocação.");
      return api.createExternalTorneio({
        name: name.trim(),
        event_date: eventDate,
        format,
        premiacao_preset_id: presetId,
        entry_fee: parseFloat(entryFee) || 0,
        notes: notes.trim() || undefined,
        tcg_game_id: Number(tcgGameId),
        placements,
      });
    },
    onSuccess: (t: { id: number }) => navigate(`/torneios/${t.id}`),
    onError: (e) => setError((e as Error).message),
  });

  const runImport = () => {
    setError("");
    mutation.mutate();
  };

  const onPlayerKeyDown = (row: PlacementRow, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    if (activeKey === row.key && hits.length > 0) {
      linkUser(row.key, hits[0]);
    }
  };

  const presetIds = presets ? Object.keys(presets.presets) : ["standard"];
  const submitDisabled = !name.trim() || !tcgGameId || filled.length < 1 || mutation.isPending;

  return (
    <div className="admin-page">
      <header className="torneio-manage-header">
        <div>
          <Link to="/torneios" className="torneio-back">
            ← Torneios
          </Link>
          <h1>Importar externo</h1>
          <p className="torneio-manage-meta">Resultados → FP · sem rodadas internas</p>
        </div>
        <div className="torneio-manage-primary">
          <button
            className="primary"
            type="button"
            disabled={submitDisabled}
            onClick={runImport}
          >
            {mutation.isPending ? "Importando…" : "Importar e atribuir FP"}
          </button>
        </div>
      </header>

      {error && <p className="error">{error}</p>}

      <form
        id="externo-form"
        onSubmit={(e) => {
          e.preventDefault();
        }}
      >
        <section className="resultado-section">
          <h2>Evento</h2>
          <div className="admin-form-grid">
            <div className="form-row">
              <label htmlFor="externo-name">Nome</label>
              <input
                id="externo-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="form-row">
              <label htmlFor="externo-tcg">TCG</label>
              <select
                id="externo-tcg"
                value={tcgGameId}
                onChange={(e) => setTcgGameId(e.target.value)}
                required
              >
                <option value="">— selecionar —</option>
                {tcgGames?.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-row">
              <label htmlFor="externo-date">Data</label>
              <input
                id="externo-date"
                type="date"
                value={eventDate}
                onChange={(e) => setEventDate(e.target.value)}
                required
              />
            </div>
            <div className="form-row">
              <label htmlFor="externo-format">Formato</label>
              <select
                id="externo-format"
                value={format}
                onChange={(e) => setFormat(e.target.value as typeof format)}
              >
                <option value="swiss">Suíço</option>
                <option value="single_elimination">Eliminatória</option>
              </select>
            </div>
            <div className="form-row">
              <label htmlFor="externo-fee">Taxa (cálculo FP)</label>
              <input
                id="externo-fee"
                value={entryFee}
                onChange={(e) => setEntryFee(e.target.value)}
                inputMode="decimal"
              />
            </div>
            <div className="form-row">
              <label htmlFor="externo-preset">Preset</label>
              <select
                id="externo-preset"
                value={presetId}
                onChange={(e) => setPresetId(e.target.value)}
              >
                {presetIds.map((id) => (
                  <option key={id} value={id}>
                    {presets?.presets[id]?.label ?? id}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <details className="admin-create-panel" style={{ marginTop: "0.75rem" }}>
            <summary>Notas (opcional)</summary>
            <div className="form-row" style={{ marginTop: "0.5rem" }}>
              <label htmlFor="externo-notes" className="sr-only">
                Notas
              </label>
              <input
                id="externo-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Local, organizador, link…"
              />
            </div>
          </details>
        </section>

        <section className="resultado-section">
          <div className="resultado-section-head">
            <h2>Colocações</h2>
            <div className="resultado-section-actions">
              <button type="button" className="secondary" onClick={addRow}>
                + linha
              </button>
            </div>
          </div>

          <div className="externo-summary">
            <span className="entre-rodadas-chip">
              {summary.total} colocação{summary.total === 1 ? "" : "ões"}
            </span>
            <span className="entre-rodadas-chip">{summary.withAccount} com conta</span>
            <span className="entre-rodadas-chip">{summary.nameOnly} só nome</span>
            {summary.drops > 0 && (
              <span className="entre-rodadas-chip">{summary.drops} drop/WO</span>
            )}
          </div>

          <div className="externo-table-wrap">
            <table className="externo-table">
              <thead>
                <tr>
                  <th className="externo-col-place">#</th>
                  <th>Jogador</th>
                  <th className="externo-col-flags">Flags</th>
                  <th className="externo-col-actions" />
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const isActive = activeKey === row.key && !row.user_id;
                  const showHits = isActive && debouncedQ.length >= 2;
                  return (
                    <tr key={row.key} className={row.is_drop ? "admin-row-inactive" : undefined}>
                      <td className="externo-col-place">
                        <strong>{row.placement}º</strong>
                      </td>
                      <td>
                        {row.user_id ? (
                          <div className="externo-linked">
                            <span className="chip-with-remove entre-rodadas-chip">
                              {row.display_name}
                              <button
                                type="button"
                                className="chip-remove"
                                aria-label="Desvincular"
                                onClick={() => clearLink(row.key)}
                              >
                                ×
                              </button>
                            </span>
                            <span className="muted externo-mode">conta</span>
                          </div>
                        ) : (
                          <div className="externo-player-cell">
                            <input
                              value={row.display_name}
                              onChange={(e) => {
                                updateRow(row.key, {
                                  display_name: e.target.value,
                                  create_account: row.showIncomplete,
                                });
                              }}
                              onFocus={() => setActiveKey(row.key)}
                              onKeyDown={(e) => onPlayerKeyDown(row, e)}
                              placeholder="Buscar conta ou digitar nome"
                              autoComplete="off"
                            />
                            {row.showIncomplete && (
                              <div className="externo-incomplete admin-form-grid">
                                <div className="form-row">
                                  <label>E-mail</label>
                                  <input
                                    type="email"
                                    value={row.email}
                                    onChange={(e) =>
                                      updateRow(row.key, {
                                        email: e.target.value,
                                        create_account: true,
                                      })
                                    }
                                    required
                                  />
                                </div>
                                <div className="form-row">
                                  <label>Celular</label>
                                  <input
                                    type="tel"
                                    value={row.phone}
                                    onChange={(e) =>
                                      updateRow(row.key, {
                                        phone: e.target.value,
                                        create_account: true,
                                      })
                                    }
                                    placeholder="11987654321"
                                    required
                                  />
                                </div>
                              </div>
                            )}
                            {showHits && hits.length > 0 && (
                              <ul className="externo-search-hits">
                                {hits.map((u) => (
                                  <li key={u.id}>
                                    <button type="button" onClick={() => linkUser(row.key, u)}>
                                      <span>{u.display_name}</span>
                                      <span className="muted">
                                        {[u.email, u.phone].filter(Boolean).join(" · ")}
                                      </span>
                                    </button>
                                  </li>
                                ))}
                              </ul>
                            )}
                            {showHits && searchDone && hits.length === 0 && (
                              <p className="field-hint">
                                Nenhuma conta. Use só o nome ou crie incomplete.
                              </p>
                            )}
                            <div className="externo-row-tools">
                              {!row.showIncomplete ? (
                                <button
                                  type="button"
                                  className="secondary"
                                  onClick={() =>
                                    updateRow(row.key, {
                                      showIncomplete: true,
                                      create_account: true,
                                    })
                                  }
                                >
                                  Incomplete
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  className="secondary"
                                  onClick={() =>
                                    updateRow(row.key, {
                                      showIncomplete: false,
                                      create_account: false,
                                      email: "",
                                      phone: "",
                                    })
                                  }
                                >
                                  Só nome
                                </button>
                              )}
                              {row.create_account && (
                                <span className="muted externo-mode">nova incomplete</span>
                              )}
                              {!row.create_account && row.display_name.trim() && (
                                <span className="muted externo-mode">só nome</span>
                              )}
                            </div>
                          </div>
                        )}
                        {row.showDecklist && (
                          <div className="form-row externo-decklist">
                            <label htmlFor={`deck-${row.key}`}>Decklist</label>
                            <textarea
                              id={`deck-${row.key}`}
                              rows={3}
                              value={row.decklist}
                              onChange={(e) => updateRow(row.key, { decklist: e.target.value })}
                              placeholder="Opcional"
                            />
                          </div>
                        )}
                      </td>
                      <td className="externo-col-flags">
                        <Switch
                          checked={row.is_drop}
                          onChange={(checked) => updateRow(row.key, { is_drop: checked })}
                        >
                          Drop/WO
                        </Switch>
                        <Switch
                          checked={row.showDecklist}
                          onChange={(checked) =>
                            updateRow(row.key, {
                              showDecklist: checked,
                              decklist: checked ? row.decklist : "",
                            })
                          }
                        >
                          Decklist
                        </Switch>
                      </td>
                      <td className="externo-col-actions">
                        <button
                          type="button"
                          className="secondary"
                          disabled={rows.length <= 1}
                          onClick={() => removeRow(row.key)}
                          aria-label={`Remover colocação ${row.placement}`}
                        >
                          Remover
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </form>
    </div>
  );
}
