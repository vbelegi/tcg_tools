import { useEffect, useId, useMemo, useState } from "react";

import { drawWinners, pickOne } from "../utils/raffle";
import type { RaffleMode } from "../utils/raffle";
import { RaffleResultModal } from "./RaffleResultModal";

type RaffleControlsProps = {
  participants: string[];
  /** Texto auxiliar acima dos controles (ex.: tamanho da pool). */
  description?: string;
  primaryButtonLabel?: string;
  compact?: boolean;
};

export function RaffleControls({
  participants,
  description,
  primaryButtonLabel = "Sortear",
  compact = false,
}: RaffleControlsProps) {
  const modeFieldId = useId();
  const [mode, setMode] = useState<RaffleMode>("batch");
  const [winnerCount, setWinnerCount] = useState("1");
  const [error, setError] = useState("");
  const [winners, setWinners] = useState<string[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [chainRemaining, setChainRemaining] = useState<string[]>([]);
  const [chainActive, setChainActive] = useState(false);

  const participantsKey = useMemo(() => participants.join("\0"), [participants]);

  useEffect(() => {
    setError("");
    setWinners([]);
    setModalOpen(false);
    setChainRemaining([]);
    setChainActive(false);
  }, [participantsKey]);

  const runBatch = () => {
    setError("");
    try {
      const count = parseInt(winnerCount, 10);
      setWinners(drawWinners(participants, count));
      setChainActive(false);
      setChainRemaining([]);
      setModalOpen(true);
    } catch (e) {
      setWinners([]);
      setModalOpen(false);
      setError((e as Error).message);
    }
  };

  const drawNextInChain = () => {
    setError("");
    try {
      const pool = chainActive ? chainRemaining : participants.slice();
      const { picked, remaining } = pickOne(pool);
      setWinners((prev) => (chainActive ? [...prev, picked] : [picked]));
      setChainRemaining(remaining);
      setChainActive(true);
      setModalOpen(true);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const resetChain = () => {
    setChainActive(false);
    setChainRemaining([]);
    setWinners([]);
    setModalOpen(false);
    setError("");
  };

  const canDraw = participants.length > 0;
  const canDrawNext = chainActive ? chainRemaining.length > 0 : canDraw;

  return (
    <div className={`raffle-controls${compact ? " raffle-controls-compact" : ""}`}>
      {description && <p className="field-hint">{description}</p>}
      {error && <p className="error">{error}</p>}

      <fieldset className="raffle-mode">
        <legend>Modo do sorteio</legend>
        <label className="checkbox-label">
          <input
            type="radio"
            name={modeFieldId}
            checked={mode === "batch"}
            onChange={() => {
              setMode("batch");
              resetChain();
            }}
          />
          Todos de uma vez
        </label>
        <label className="checkbox-label">
          <input
            type="radio"
            name={modeFieldId}
            checked={mode === "chain"}
            onChange={() => {
              setMode("chain");
              resetChain();
            }}
          />
          Encadeado (1 a 1)
        </label>
      </fieldset>

      {mode === "batch" ? (
        <div className="raffle-batch-row">
          <div className="form-row raffle-count-row">
            <label htmlFor={`${modeFieldId}-count`}>Sorteados</label>
            <input
              id={`${modeFieldId}-count`}
              type="number"
              min={1}
              max={Math.max(1, participants.length)}
              value={winnerCount}
              onChange={(e) => setWinnerCount(e.target.value)}
              disabled={!canDraw}
            />
          </div>
          <button
            className="primary"
            type="button"
            onClick={runBatch}
            disabled={!canDraw}
          >
            {primaryButtonLabel}
          </button>
        </div>
      ) : (
        <>
          <p className="field-hint">
            {chainActive
              ? `Já sorteados: ${winners.length} · Restam: ${chainRemaining.length}`
              : `Pool: ${participants.length}. Cada clique sorteia um sem repetir.`}
          </p>
          {chainActive && winners.length > 0 && (
            <ol className="raffle-winners raffle-winners-inline">
              {winners.map((name, i) => (
                <li key={`${i}-${name}`}>
                  <span className="raffle-winners-rank">Sorteado {i + 1}</span>
                  <span className="raffle-winners-name">{name}</span>
                </li>
              ))}
            </ol>
          )}
          {!modalOpen && (
            <div className="raffle-chain-actions">
              <button
                className="primary"
                type="button"
                onClick={drawNextInChain}
                disabled={!canDrawNext}
              >
                {chainActive ? "Sortear próximo" : "Sortear o 1º"}
              </button>
              {chainActive && (
                <button className="secondary" type="button" onClick={resetChain}>
                  Reiniciar
                </button>
              )}
            </div>
          )}
        </>
      )}

      <RaffleResultModal
        open={modalOpen}
        winners={winners}
        mode={mode}
        remainingCount={mode === "chain" ? chainRemaining.length : undefined}
        onClose={() => setModalOpen(false)}
        onRedraw={mode === "batch" ? runBatch : undefined}
        onDrawNext={mode === "chain" && chainRemaining.length > 0 ? drawNextInChain : undefined}
        onRestartChain={mode === "chain" && chainActive ? resetChain : undefined}
      />
    </div>
  );
}
