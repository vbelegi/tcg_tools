import { useEffect } from "react";

import { Modal } from "./Modal";
import type { RaffleMode } from "../utils/raffle";

type RaffleResultModalProps = {
  open: boolean;
  winners: string[];
  onClose: () => void;
  mode?: RaffleMode;
  remainingCount?: number;
  onRedraw?: () => void;
  onDrawNext?: () => void;
  onRestartChain?: () => void;
  redrawPending?: boolean;
};

export function RaffleResultModal({
  open,
  winners,
  onClose,
  mode = "batch",
  remainingCount,
  onRedraw,
  onDrawNext,
  onRestartChain,
  redrawPending,
}: RaffleResultModalProps) {
  const latest = winners.length > 0 ? winners[winners.length - 1] : null;

  useEffect(() => {
    if (!open || mode !== "chain" || !onDrawNext || redrawPending) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      const target = e.target as HTMLElement | null;
      if (target && typeof target.closest === "function") {
        if (target.closest("button, input, textarea, select, a")) return;
      }
      e.preventDefault();
      onDrawNext();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, mode, onDrawNext, redrawPending]);

  return (
    <Modal
      open={open}
      title={mode === "chain" ? "Sorteio encadeado" : "Resultado do sorteio"}
      onClose={onClose}
      footer={
        <>
          {mode === "chain" && onDrawNext && (
            <button className="secondary" onClick={onDrawNext} disabled={redrawPending}>
              Sortear próximo
            </button>
          )}
          {mode === "chain" && onRestartChain && (
            <button className="secondary" onClick={onRestartChain} disabled={redrawPending}>
              Reiniciar
            </button>
          )}
          {mode === "batch" && onRedraw && (
            <button className="secondary" onClick={onRedraw} disabled={redrawPending}>
              Sortear novamente
            </button>
          )}
          <button className="primary" onClick={onClose}>
            Fechar
          </button>
        </>
      }
    >
      {winners.length === 0 ? (
        <p>Nenhum sorteado.</p>
      ) : mode === "chain" ? (
        <>
          {latest && (
            <p className="raffle-latest">
              Sorteado agora: <strong>{latest}</strong>
            </p>
          )}
          {remainingCount != null && (
            <p style={{ fontSize: "0.9rem", opacity: 0.85, marginTop: 0 }}>
              Restam {remainingCount} na pool
              {remainingCount === 0 ? " — encadeamento completo." : "."}
              {remainingCount > 0 ? " Enter ou Espaço sorteia o próximo." : ""}
            </p>
          )}
          <ol className="raffle-winners">
            {winners.map((name, i) => (
              <li key={`${i}-${name}`}>
                <span className="raffle-winners-rank">Sorteado {i + 1}</span>
                <span className="raffle-winners-name">{name}</span>
              </li>
            ))}
          </ol>
        </>
      ) : (
        <ol className="raffle-winners">
          {winners.map((name, i) => (
            <li key={`${i}-${name}`}>
              <span className="raffle-winners-rank">Sorteado {i + 1}</span>
              <span className="raffle-winners-name">{name}</span>
            </li>
          ))}
        </ol>
      )}
    </Modal>
  );
}
