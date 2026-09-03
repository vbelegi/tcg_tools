import { useId, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import type { PromoDrawResult, PromoParticipant } from "../api/types";
import { pickOne } from "../utils/raffle";
import { RaffleResultModal } from "./RaffleResultModal";

type Props = {
  actionId: number;
  onDrawn: (result: PromoDrawResult) => void;
};

type PoolMember = { user_id: number; display_name: string };

export function PromoRafflePanel({ actionId, onDrawn }: Props) {
  const modeFieldId = useId();
  const [mode, setMode] = useState<"direct" | "chained">("direct");
  const [winnerCount, setWinnerCount] = useState("1");
  const [error, setError] = useState("");
  const [chainWinners, setChainWinners] = useState<PoolMember[]>([]);
  const [chainRemaining, setChainRemaining] = useState<PoolMember[]>([]);
  const [chainActive, setChainActive] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const { data: participants } = useQuery({
    queryKey: ["acao-participants", actionId],
    queryFn: () => api.listPromoParticipants(actionId),
  });

  const pool: PoolMember[] = useMemo(
    () =>
      (participants ?? [])
        .filter((row: PromoParticipant) => row.status === "confirmed")
        .map((row) => ({ user_id: row.user_id, display_name: row.display_name })),
    [participants],
  );

  const resetChain = () => {
    setChainActive(false);
    setChainRemaining([]);
    setChainWinners([]);
    setModalOpen(false);
    setError("");
  };

  const persist = useMutation({
    mutationFn: (body: {
      mode: "direct" | "chained";
      winner_count?: number;
      winner_user_ids?: number[];
    }) => api.drawPromoAction(actionId, body),
    onSuccess: (result) => {
      resetChain();
      onDrawn(result);
    },
    onError: (e) => setError((e as Error).message),
  });

  const runDirect = () => {
    setError("");
    const count = parseInt(winnerCount, 10);
    persist.mutate({ mode: "direct", winner_count: count });
  };

  const drawNextInChain = () => {
    setError("");
    try {
      const current = chainActive ? chainRemaining : pool.slice();
      const { picked, remaining } = pickOne(current);
      setChainWinners((prev) => (chainActive ? [...prev, picked] : [picked]));
      setChainRemaining(remaining);
      setChainActive(true);
      setModalOpen(true);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const confirmChain = () => {
    setError("");
    persist.mutate({
      mode: "chained",
      winner_user_ids: chainWinners.map((w) => w.user_id),
    });
  };

  const canDraw = pool.length > 0;
  const canDrawNext = chainActive ? chainRemaining.length > 0 : canDraw;

  return (
    <section className="promo-raffle">
      <h2>Sorteio</h2>
      <p className="field-hint">
        Pool confirmada: {pool.length}. O resultado é gravado uma única vez.
      </p>
      {error && <p className="error">{error}</p>}

      <fieldset className="raffle-mode">
        <legend>Modo do sorteio</legend>
        <label className="checkbox-label">
          <input
            type="radio"
            name={modeFieldId}
            checked={mode === "direct"}
            onChange={() => {
              setMode("direct");
              resetChain();
            }}
          />
          Todos de uma vez
        </label>
        <label className="checkbox-label">
          <input
            type="radio"
            name={modeFieldId}
            checked={mode === "chained"}
            onChange={() => {
              setMode("chained");
              resetChain();
            }}
          />
          Encadeado (1 a 1)
        </label>
      </fieldset>

      {mode === "direct" ? (
        <div className="raffle-batch-row">
          <div className="form-row raffle-count-row">
            <label htmlFor={`${modeFieldId}-count`}>Sorteados</label>
            <input
              id={`${modeFieldId}-count`}
              type="number"
              min={1}
              max={Math.max(1, pool.length)}
              value={winnerCount}
              onChange={(e) => setWinnerCount(e.target.value)}
              disabled={!canDraw || persist.isPending}
            />
          </div>
          <button
            className="primary"
            type="button"
            onClick={runDirect}
            disabled={!canDraw || persist.isPending}
          >
            {persist.isPending ? "Sorteando…" : "Sortear"}
          </button>
        </div>
      ) : (
        <>
          <p className="field-hint">
            {chainActive
              ? `Já sorteados: ${chainWinners.length} · Restam: ${chainRemaining.length}`
              : `Cada clique sorteia um sem repetir. Confirme para gravar.`}
          </p>
          {chainActive && chainWinners.length > 0 && (
            <ol className="raffle-winners raffle-winners-inline">
              {chainWinners.map((row, i) => (
                <li key={`${i}-${row.user_id}`}>
                  <span className="raffle-winners-rank">Sorteado {i + 1}</span>
                  <span className="raffle-winners-name">{row.display_name}</span>
                </li>
              ))}
            </ol>
          )}
          <div className="raffle-chain-actions">
            <button
              className="primary"
              type="button"
              onClick={drawNextInChain}
              disabled={!canDrawNext || persist.isPending}
            >
              {chainActive ? "Sortear próximo" : "Sortear o 1º"}
            </button>
            {chainActive && (
              <button className="secondary" type="button" onClick={resetChain} disabled={persist.isPending}>
                Reiniciar
              </button>
            )}
            {chainWinners.length > 0 && (
              <button
                className="primary"
                type="button"
                onClick={confirmChain}
                disabled={persist.isPending}
              >
                {persist.isPending ? "Gravando…" : "Confirmar sorteio"}
              </button>
            )}
          </div>
        </>
      )}

      <RaffleResultModal
        open={modalOpen}
        winners={chainWinners.map((w) => w.display_name)}
        mode="chain"
        remainingCount={chainRemaining.length}
        onClose={() => setModalOpen(false)}
        onDrawNext={chainRemaining.length > 0 ? drawNextInChain : undefined}
        onRestartChain={chainActive ? resetChain : undefined}
      />
    </section>
  );
}
