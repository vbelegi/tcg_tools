import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PremiacaoBandsTable } from "../../components/PremiacaoBandsTable";
import { RaffleControls } from "../../components/RaffleControls";
import { api } from "../../api/client";
import { isStaffRole } from "../../utils/roles";
import { creditosSanityMismatch, sumCreditosFromRows } from "../../utils/premiacao";

const TIEBREAKER_TOOLTIP = [
  "Ordem de desempate (Suíço):",
  "1. Pontos de partida",
  "2. OMW% — % de vitórias em partidas dos oponentes",
  "3. GW% — % de vitórias em games do jogador",
  "4. OGW% — % de vitórias em games dos oponentes",
  "5. Seed (menor)",
  "6. Ordem de inscrição (mais cedo)",
].join("\n");

function formatPct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function TorneioResultadoPage() {
  const { id } = useParams<{ id: string }>();
  const eventId = Number(id);
  const qc = useQueryClient();

  const { data: me, isFetched: meFetched } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const isStaff = Boolean(me && isStaffRole(me.role));
  const isGuest = meFetched && !me;

  const [decklists, setDecklists] = useState<Record<number, string>>({});
  const [deckMeta, setDeckMeta] = useState<
    Record<
      number,
      {
        source: string;
        source_id: string;
        source_url: string;
        name: string | null;
        format: string | null;
        price_low_brl: number | null;
      }
    >
  >({});
  const [importUrl, setImportUrl] = useState<Record<number, string>>({});
  const [importError, setImportError] = useState<Record<number, string>>({});
  const [importingId, setImportingId] = useState<number | null>(null);
  const [decklistsSaved, setDecklistsSaved] = useState(false);
  const [exportError, setExportError] = useState("");
  const [raffleExcludedIds, setRaffleExcludedIds] = useState<number[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!decklistsSaved) return;
    const t = window.setTimeout(() => setDecklistsSaved(false), 2500);
    return () => window.clearTimeout(t);
  }, [decklistsSaved]);

  const { data: torneio, isError, error, isLoading: torneioLoading } = useQuery({
    queryKey: ["torneio", eventId],
    queryFn: () => api.getTorneio(eventId),
  });

  const { data: classificacao } = useQuery({
    queryKey: ["classificacao", eventId],
    queryFn: () => api.getClassificacao(eventId),
    enabled: Boolean(torneio),
  });

  const { data: premiacao } = useQuery({
    queryKey: ["premiacao-torneio", eventId],
    queryFn: () => api.getPremiacao(eventId),
    enabled: Boolean(torneio),
  });

  useEffect(() => {
    if (!classificacao?.standings) return;
    const texts: Record<number, string> = {};
    const meta: typeof deckMeta = {};
    for (const s of classificacao.standings) {
      texts[s.player_id] = s.decklist ?? "";
      if (s.decklist_source && s.decklist_source_id && s.decklist_source_url) {
        meta[s.player_id] = {
          source: s.decklist_source,
          source_id: s.decklist_source_id,
          source_url: s.decklist_source_url,
          name: s.decklist_name ?? null,
          format: s.decklist_format ?? null,
          price_low_brl:
            s.decklist_price_low_brl == null ? null : Number(s.decklist_price_low_brl),
        };
      }
    }
    setDecklists(texts);
    setDeckMeta(meta);
  }, [classificacao]);

  const saveDecklists = useMutation({
    mutationFn: () =>
      api.updateDecklists(
        eventId,
        Object.entries(decklists).map(([player_id, decklist]) => {
          const pid = Number(player_id);
          const meta = deckMeta[pid];
          return {
            player_id: pid,
            decklist: decklist || null,
            ...(meta
              ? {
                  decklist_source: meta.source,
                  decklist_source_id: meta.source_id,
                  decklist_source_url: meta.source_url,
                  decklist_name: meta.name,
                  decklist_format: meta.format,
                  decklist_price_low_brl: meta.price_low_brl,
                }
              : {}),
          };
        }),
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["classificacao", eventId] });
      setDecklistsSaved(true);
    },
  });

  const importDeck = async (playerId: number) => {
    const url = (importUrl[playerId] || "").trim();
    if (!url) {
      setImportError((e) => ({ ...e, [playerId]: "Cole a URL do deck na LigaMagic." }));
      return;
    }
    setImportingId(playerId);
    setImportError((e) => ({ ...e, [playerId]: "" }));
    try {
      const preview = await api.previewDeckImport(url);
      const price =
        preview.price_low_brl == null ? null : Number(preview.price_low_brl);
      setDecklists((d) => ({ ...d, [playerId]: preview.plain_text }));
      setDeckMeta((m) => ({
        ...m,
        [playerId]: {
          source: preview.source,
          source_id: preview.source_deck_id,
          source_url: preview.source_url,
          name: preview.name,
          format: preview.format,
          price_low_brl: Number.isFinite(price as number) ? (price as number) : null,
        },
      }));
    } catch (err) {
      setImportError((e) => ({
        ...e,
        [playerId]: err instanceof Error ? err.message : "Falha ao importar",
      }));
    } finally {
      setImportingId(null);
    }
  };

  const handleExport = async () => {
    setExportError("");
    setMenuOpen(false);
    try {
      await api.exportLog(eventId);
    } catch (e) {
      setExportError((e as Error).message);
    }
  };

  const prem = premiacao as {
    premios: number[];
    creditos?: number[] | null;
    total_creditos?: number | null;
    entry_fee?: number;
    bands?: Array<{ label: string; pool: number; payout_per_player?: number | null }>;
    player_payouts?: Array<{ player_id: number; name: string; band_label: string; payout: number }>;
  } | undefined;

  const showCreditos = prem && (prem.entry_fee ?? 0) > 0;
  const totalCreditos =
    prem?.total_creditos ??
    (showCreditos
      ? sumCreditosFromRows(prem?.creditos, prem?.player_payouts, prem?.entry_fee ?? 0)
      : null);
  const useBands = prem?.bands && prem.bands.length > 0;

  const creditosSumFromRows =
    showCreditos && prem
      ? sumCreditosFromRows(prem.creditos, prem.player_payouts, prem.entry_fee ?? 0)
      : null;
  const creditosMismatch = creditosSanityMismatch(totalCreditos, creditosSumFromRows);

  const baseRaffleCandidates = useMemo(
    () => classificacao?.standings.filter((s) => !s.is_drop) ?? [],
    [classificacao],
  );

  const validCandidateIds = useMemo(
    () => new Set(baseRaffleCandidates.map((s) => s.player_id)),
    [baseRaffleCandidates],
  );

  useEffect(() => {
    setRaffleExcludedIds((prev) => prev.filter((id) => validCandidateIds.has(id)));
  }, [validCandidateIds]);

  const rafflePool = baseRaffleCandidates.filter((s) => !raffleExcludedIds.includes(s.player_id));
  const raffleNames = rafflePool.map((s) => s.name);

  const toggleRaffleExclusion = (playerId: number, include: boolean) => {
    setRaffleExcludedIds((prev) => {
      if (include) return prev.filter((id) => id !== playerId);
      if (prev.includes(playerId)) return prev;
      return [...prev, playerId];
    });
  };

  const excludeFirstPlace = () => {
    const first = baseRaffleCandidates.find((s) => s.rank === 1);
    if (!first) return;
    setRaffleExcludedIds((prev) =>
      prev.includes(first.player_id) ? prev : [...prev, first.player_id],
    );
  };

  if (torneioLoading || !meFetched) return <p>Carregando...</p>;
  if (isError || !torneio) {
    return <p className="error">{(error as Error)?.message || "Torneio não encontrado."}</p>;
  }

  const playerCount = classificacao?.standings.length ?? torneio.player_count;
  const backTo = isGuest ? "/torneios" : `/torneios/${eventId}`;

  return (
    <div className="resultado-page">
      <header className="torneio-manage-header">
        <div>
          <Link to={backTo} className="torneio-back">
            ← {isGuest ? "Torneios" : torneio.name}
          </Link>
          <div className="torneio-manage-title-row">
            <h1>Resultado final</h1>
            {isStaff && torneio.status === "finished" && (
              <div className="torneio-overflow">
                <button
                  type="button"
                  className="secondary torneio-overflow-btn"
                  aria-expanded={menuOpen}
                  onClick={() => setMenuOpen((v) => !v)}
                >
                  ⋯
                </button>
                {menuOpen && (
                  <div className="torneio-overflow-menu" role="menu">
                    <button type="button" role="menuitem" onClick={handleExport}>
                      Exportar log JSON
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
          <p className="torneio-manage-meta">
            {torneio.name} · {torneio.event_date}
            {playerCount != null ? ` · ${playerCount} jogador(es)` : ""}
          </p>
          {exportError && <p className="error">{exportError}</p>}
        </div>
      </header>

      <section className="resultado-section">
        <div className="resultado-section-head">
          <h2 className="standings-heading">
            Classificação
            <span className="help-tip" tabIndex={0}>
              <span className="help-tip-icon" aria-hidden="true">
                ?
              </span>
              <span className="sr-only">Critérios de desempate</span>
              <span className="help-tip-content" role="tooltip">
                {TIEBREAKER_TOOLTIP}
              </span>
            </span>
          </h2>
        </div>

        {classificacao && (
          <div className="resultado-table-wrap">
            <table className="resultado-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Jogador</th>
                  <th title="Pontos de partida">Pts</th>
                  <th title="Opponent Match Win %">OMW%</th>
                  <th title="Game Win %">GW%</th>
                  <th title="Opponent Game Win %">OGW%</th>
                  <th>Decklist</th>
                </tr>
              </thead>
              <tbody>
                {classificacao.standings.map((s) => {
                  const top = !s.is_drop && s.rank <= 3;
                  return (
                    <tr key={s.player_id} className={top ? `resultado-row-top-${s.rank}` : undefined}>
                      <td className="resultado-rank-cell">
                        <span className="resultado-rank-badge">
                          {s.rank_label ?? s.rank}
                        </span>
                      </td>
                      <td className="resultado-player-cell">{s.name}</td>
                      <td>{s.is_drop ? "—" : s.points}</td>
                      <td>{s.is_drop ? "—" : formatPct(s.omw)}</td>
                      <td>{s.is_drop ? "—" : formatPct(s.gw)}</td>
                      <td>{s.is_drop ? "—" : formatPct(s.ogw)}</td>
                      <td className="resultado-deck-cell">
                        {s.is_drop ? (
                          "—"
                        ) : isStaff ? (
                          <div className="resultado-deck-edit">
                            <textarea
                              className="resultado-deck-input"
                              rows={3}
                              placeholder="Lista em texto ou importe da LigaMagic"
                              value={decklists[s.player_id] ?? ""}
                              onChange={(e) =>
                                setDecklists({ ...decklists, [s.player_id]: e.target.value })
                              }
                            />
                            <div className="resultado-deck-import">
                              <input
                                type="url"
                                className="resultado-deck-input"
                                placeholder="URL LigaMagic"
                                value={importUrl[s.player_id] ?? ""}
                                onChange={(e) =>
                                  setImportUrl({ ...importUrl, [s.player_id]: e.target.value })
                                }
                              />
                              <button
                                type="button"
                                className="secondary"
                                disabled={importingId === s.player_id}
                                onClick={() => importDeck(s.player_id)}
                              >
                                {importingId === s.player_id ? "Importando…" : "Importar"}
                              </button>
                            </div>
                            {importError[s.player_id] ? (
                              <p className="error" style={{ margin: "0.25rem 0 0" }}>
                                {importError[s.player_id]}
                              </p>
                            ) : null}
                            {deckMeta[s.player_id] ? (
                              <p className="field-hint" style={{ margin: "0.25rem 0 0" }}>
                                {deckMeta[s.player_id].name
                                  ? `${deckMeta[s.player_id].name}`
                                  : "Importado"}
                                {deckMeta[s.player_id].format
                                  ? ` · ${deckMeta[s.player_id].format}`
                                  : ""}
                                {deckMeta[s.player_id].price_low_brl != null
                                  ? ` · R$ ${Number(deckMeta[s.player_id].price_low_brl).toFixed(2)} (menor)`
                                  : ""}
                              </p>
                            ) : null}
                            {s.decklist ? (
                              <p style={{ margin: "0.35rem 0 0" }}>
                                <Link
                                  className="secondary"
                                  to={`/torneios/${eventId}/jogadores/${s.player_id}/deck`}
                                >
                                  Ver deck
                                </Link>
                              </p>
                            ) : null}
                          </div>
                        ) : s.decklist ? (
                          <div>
                            {(s.decklist_name ||
                              s.decklist_format ||
                              s.decklist_price_low_brl != null) && (
                              <p className="field-hint" style={{ marginTop: 0 }}>
                                {[
                                  s.decklist_name,
                                  s.decklist_format,
                                  s.decklist_price_low_brl != null
                                    ? `R$ ${Number(s.decklist_price_low_brl).toFixed(2)}`
                                    : null,
                                ]
                                  .filter(Boolean)
                                  .join(" · ")}
                              </p>
                            )}
                            <Link
                              className="secondary resultado-deck-link"
                              to={`/torneios/${eventId}/jogadores/${s.player_id}/deck`}
                            >
                              Ver deck
                            </Link>
                          </div>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {isStaff && (
          <div className="resultado-section-actions">
            <button
              className="secondary"
              type="button"
              onClick={() => saveDecklists.mutate()}
              disabled={saveDecklists.isPending}
            >
              {saveDecklists.isPending ? "Salvando…" : "Salvar decklists"}
            </button>
            {decklistsSaved && (
              <span className="save-feedback success" role="status">
                Salvo
              </span>
            )}
          </div>
        )}
      </section>

      <section className="resultado-section">
        <h2>Premiação</h2>

        {torneio.entry_fee === 0 && (
          <p className="warning">
            Inscrição R$ 0 — sem pot a distribuir.
            {isStaff && " Use a aba Premiação para calcular split isolado."}
          </p>
        )}

        {prem && useBands && (
          <>
            <div className="resultado-table-wrap resultado-table-wrap-narrow">
              <PremiacaoBandsTable
                bands={prem.bands!}
                playerPayouts={prem.player_payouts}
                entryFee={prem.entry_fee}
              />
            </div>
            {showCreditos && totalCreditos != null && (
              <p className="resultado-total">
                Total em créditos na loja: <strong>R$ {totalCreditos.toFixed(2)}</strong>
                {creditosSumFromRows != null && (
                  <span className="muted"> (soma linhas: R$ {creditosSumFromRows.toFixed(2)})</span>
                )}
              </p>
            )}
            {creditosMismatch && (
              <p className="warning" role="alert">
                Atenção: total de créditos difere da soma por jogador — verifique premiação.
              </p>
            )}
          </>
        )}

        {prem && !useBands && (
          <div className="resultado-table-wrap resultado-table-wrap-narrow">
            <table className="resultado-table">
              <thead>
                <tr>
                  <th>Colocação</th>
                  <th>Inscrições</th>
                  {showCreditos && <th>Créditos na Loja</th>}
                </tr>
              </thead>
              <tbody>
                {prem.premios.map((p, i) => (
                  <tr key={i}>
                    <td>{i + 1}º</td>
                    <td>{p}</td>
                    {showCreditos && (
                      <td>R$ {(prem.creditos?.[i] ?? p * (prem.entry_fee ?? 0)).toFixed(2)}</td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {prem && !useBands && showCreditos && totalCreditos != null && (
          <p className="resultado-total">
            Total em créditos na loja: <strong>R$ {totalCreditos.toFixed(2)}</strong>
          </p>
        )}
      </section>

      {isStaff && (
        <section className="resultado-section">
          <div className="resultado-section-head">
            <div>
              <h2>Sorteio</h2>
              <p className="field-hint">
                Base: jogadores sem drop ({baseRaffleCandidates.length}). Toque nos chips para
                incluir/excluir da pool (ex.: tire o campeão).
              </p>
            </div>
            {baseRaffleCandidates.length > 0 && (
              <div className="resultado-section-actions">
                <button className="secondary" type="button" onClick={excludeFirstPlace}>
                  Excluir 1º lugar
                </button>
                <button
                  className="secondary"
                  type="button"
                  onClick={() => setRaffleExcludedIds([])}
                  disabled={raffleExcludedIds.length === 0}
                >
                  Incluir todos
                </button>
              </div>
            )}
          </div>

          {baseRaffleCandidates.length > 0 && (
            <ul className="entre-rodadas-chips raffle-chips">
              {baseRaffleCandidates.map((s) => {
                const included = !raffleExcludedIds.includes(s.player_id);
                return (
                  <li key={s.player_id}>
                    <button
                      type="button"
                      className={`entre-rodadas-chip raffle-chip${included ? " raffle-chip-on" : ""}`}
                      aria-pressed={included}
                      onClick={() => toggleRaffleExclusion(s.player_id, !included)}
                    >
                      {s.rank}º {s.name}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}

          <RaffleControls
            participants={raffleNames}
            description={`Pool: ${raffleNames.length} jogador(es)${
              raffleExcludedIds.length > 0 ? ` · ${raffleExcludedIds.length} excluído(s)` : ""
            }`}
            primaryButtonLabel="Sortear"
            compact
          />
        </section>
      )}
    </div>
  );
}
