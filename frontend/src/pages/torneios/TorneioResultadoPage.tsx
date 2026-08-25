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

  const [decklists, setDecklists] = useState<Record<number, string>>({});
  const [decklistsSaved, setDecklistsSaved] = useState(false);
  const [exportError, setExportError] = useState("");
  const [raffleExcludedIds, setRaffleExcludedIds] = useState<number[]>([]);

  useEffect(() => {
    if (!decklistsSaved) return;
    const t = window.setTimeout(() => setDecklistsSaved(false), 2500);
    return () => window.clearTimeout(t);
  }, [decklistsSaved]);

  const { data: torneio } = useQuery({
    queryKey: ["torneio", eventId],
    queryFn: () => api.getTorneio(eventId),
  });

  const { data: classificacao } = useQuery({
    queryKey: ["classificacao", eventId],
    queryFn: () => api.getClassificacao(eventId),
  });

  const { data: premiacao } = useQuery({
    queryKey: ["premiacao-torneio", eventId],
    queryFn: () => api.getPremiacao(eventId),
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

  return (
    <div>
      <Link to={`/torneios/${eventId}`}>← Voltar</Link>
      <h1>Resultado final</h1>

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

      {classificacao && (
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Jogador</th>
              <th title="Pontos de partida">Pts</th>
              <th title="Opponent Match Win % — % de vitórias em partidas dos oponentes">OMW%</th>
              <th title="Game Win % — % de vitórias em games do jogador">GW%</th>
              <th title="Opponent Game Win % — % de vitórias em games dos oponentes">OGW%</th>
              <th>Decklist (opcional)</th>
            </tr>
          </thead>
          <tbody>
            {classificacao.standings.map((s) => (
              <tr key={s.player_id}>
                <td>{s.rank_label ?? s.rank}</td>
                <td>{s.name}</td>
                <td>{s.is_drop ? "—" : s.points}</td>
                <td>{s.is_drop ? "—" : formatPct(s.omw)}</td>
                <td>{s.is_drop ? "—" : formatPct(s.gw)}</td>
                <td>{s.is_drop ? "—" : formatPct(s.ogw)}</td>
                <td>
                  {!s.is_drop && (
                    <input
                      placeholder="Nome ou URL"
                      defaultValue={s.decklist ?? ""}
                      onChange={(e) =>
                        setDecklists({ ...decklists, [s.player_id]: e.target.value })
                      }
                    />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: "1rem" }}>
        <button
          className="secondary"
          onClick={() => saveDecklists.mutate()}
          disabled={saveDecklists.isPending}
        >
          {saveDecklists.isPending ? "Salvando…" : "Salvar decklists"}
        </button>
        {decklistsSaved && (
          <div className="save-feedback success" role="status">
            Salvo com sucesso
          </div>
        )}
      </div>

      <h2 style={{ marginTop: "2rem" }}>Premiação</h2>

      {torneio && torneio.entry_fee === 0 && (
        <p className="warning">
          Inscrição R$ 0 — sem pot a distribuir. Use a aba Premiação para calcular split isolado.
        </p>
      )}

      {prem && useBands && (
        <>
          <PremiacaoBandsTable
            bands={prem.bands!}
            playerPayouts={prem.player_payouts}
            entryFee={prem.entry_fee}
          />
          {showCreditos && totalCreditos != null && (
            <p style={{ marginTop: "0.75rem" }}>
              Total em créditos na loja: <strong>R$ {totalCreditos.toFixed(2)}</strong>
              {creditosSumFromRows != null && (
                <span style={{ opacity: 0.85 }}>
                  {" "}
                  (soma linhas: R$ {creditosSumFromRows.toFixed(2)})
                </span>
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
        <table>
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
      )}

      {prem && !useBands && showCreditos && totalCreditos != null && (
        <p style={{ marginTop: "0.75rem" }}>
          Total em créditos na loja: <strong>R$ {totalCreditos.toFixed(2)}</strong>
        </p>
      )}

      <h2 style={{ marginTop: "2rem" }}>Sorteio</h2>
      <p style={{ fontSize: "0.9rem", opacity: 0.85 }}>
        Base: jogadores sem drop ({baseRaffleCandidates.length}). Marque quem entra na pool do
        sorteio (ex.: desmarque o campeão).
      </p>

      {baseRaffleCandidates.length > 0 && (
        <div className="raffle-pool">
          <div className="raffle-pool-actions">
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
          <ul className="raffle-pool-list">
            {baseRaffleCandidates.map((s) => {
              const included = !raffleExcludedIds.includes(s.player_id);
              return (
                <li key={s.player_id}>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={included}
                      onChange={(e) => toggleRaffleExclusion(s.player_id, e.target.checked)}
                    />
                    <span>
                      {s.rank}º — {s.name}
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <RaffleControls
        participants={raffleNames}
        description={`Pool do sorteio: ${raffleNames.length} jogador(es)${
          raffleExcludedIds.length > 0 ? ` (${raffleExcludedIds.length} excluído(s))` : ""
        }.`}
        primaryButtonLabel="Sortear entre jogadores do torneio"
      />

      {torneio?.status === "finished" && (
        <>
          <button className="primary" style={{ marginTop: "1.5rem" }} onClick={handleExport}>
            Exportar log JSON
          </button>
          {exportError && <p className="error">{exportError}</p>}
        </>
      )}
    </div>
  );
}
