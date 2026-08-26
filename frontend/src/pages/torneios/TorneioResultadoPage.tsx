import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PremiacaoBandsTable } from "../../components/PremiacaoBandsTable";
import { RaffleControls } from "../../components/RaffleControls";
import { api } from "../../api/client";
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
  const isStaff = Boolean(me && (me.role === "admin" || me.role === "staff"));
  const isGuest = meFetched && !me;

  const [decklists, setDecklists] = useState<Record<number, string>>({});
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

  const saveDecklists = useMutation({
    mutationFn: () =>
      api.updateDecklists(
        eventId,
        Object.entries(decklists).map(([player_id, decklist]) => ({
          player_id: Number(player_id),
          decklist: decklist || null,
        })),
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["classificacao", eventId] });
      setDecklistsSaved(true);
    },
  });

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
                          <input
                            className="resultado-deck-input"
                            placeholder="Nome ou URL"
                            defaultValue={s.decklist ?? ""}
                            onChange={(e) =>
                              setDecklists({ ...decklists, [s.player_id]: e.target.value })
                            }
                          />
                        ) : s.decklist ? (
                          s.decklist.startsWith("http") ? (
                            <a href={s.decklist} target="_blank" rel="noreferrer">
                              Link
                            </a>
                          ) : (
                            s.decklist
                          )
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
