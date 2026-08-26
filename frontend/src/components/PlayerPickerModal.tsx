import { useEffect, useMemo, useState } from "react";

import { Modal } from "./Modal";

export type PlayerOption = { id: number; name: string };

type PlayerPickerModalProps = {
  open: boolean;
  title: string;
  description: string;
  players: PlayerOption[];
  confirmLabel?: string;
  pending?: boolean;
  /** When true, confirm requires a second step typing the player name. */
  requireNameConfirm?: boolean;
  onConfirm: (playerId: number) => void;
  onClose: () => void;
};

function namesMatch(typed: string, expected: string): boolean {
  return typed.trim().toLocaleLowerCase("pt-BR") === expected.trim().toLocaleLowerCase("pt-BR");
}

export function PlayerPickerModal({
  open,
  title,
  description,
  players,
  confirmLabel = "Confirmar",
  pending = false,
  requireNameConfirm = false,
  onConfirm,
  onClose,
}: PlayerPickerModalProps) {
  const [selectedId, setSelectedId] = useState<string>("");
  const [step, setStep] = useState<"select" | "confirm">("select");
  const [typedName, setTypedName] = useState("");

  useEffect(() => {
    if (!open) return;
    setSelectedId(players.length === 1 ? String(players[0].id) : "");
    setStep("select");
    setTypedName("");
  }, [open, players]);

  const selectedPlayer = useMemo(
    () => players.find((p) => String(p.id) === selectedId) ?? null,
    [players, selectedId],
  );

  const nameOk = selectedPlayer != null && namesMatch(typedName, selectedPlayer.name);

  const handleConfirm = () => {
    if (!selectedId) return;
    if (requireNameConfirm && !nameOk) return;
    onConfirm(Number(selectedId));
  };

  const footer =
    requireNameConfirm && step === "confirm" ? (
      <>
        <button
          type="button"
          className="secondary"
          onClick={() => {
            setStep("select");
            setTypedName("");
          }}
          disabled={pending}
        >
          Voltar
        </button>
        <button
          type="button"
          className="danger"
          onClick={handleConfirm}
          disabled={pending || !nameOk}
        >
          {confirmLabel}
        </button>
      </>
    ) : requireNameConfirm ? (
      <>
        <button type="button" className="secondary" onClick={onClose} disabled={pending}>
          Cancelar
        </button>
        <button
          type="button"
          className="primary"
          onClick={() => setStep("confirm")}
          disabled={pending || !selectedId}
        >
          Continuar
        </button>
      </>
    ) : (
      <>
        <button type="button" className="secondary" onClick={onClose} disabled={pending}>
          Cancelar
        </button>
        <button
          type="button"
          className="danger"
          onClick={handleConfirm}
          disabled={pending || !selectedId}
        >
          {confirmLabel}
        </button>
      </>
    );

  return (
    <Modal open={open} title={title} onClose={onClose} footer={footer}>
      <p className="modal-message">{description}</p>
      {requireNameConfirm && step === "confirm" && selectedPlayer ? (
        <div className="form-row">
          <p className="field-hint">
            Você está prestes a confirmar <strong>{selectedPlayer.name}</strong>. Digite o nome
            exatamente para continuar.
          </p>
          <label htmlFor="player-picker-confirm-name">Digite o nome do jogador</label>
          <input
            id="player-picker-confirm-name"
            type="text"
            autoComplete="off"
            autoFocus
            value={typedName}
            onChange={(e) => setTypedName(e.target.value)}
            disabled={pending}
            placeholder={selectedPlayer.name}
          />
        </div>
      ) : (
        <div className="form-row">
          <label htmlFor="player-picker-select">Jogador</label>
          <select
            id="player-picker-select"
            className="modal-select"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            disabled={pending || players.length === 0}
          >
            <option value="">Selecione…</option>
            {players.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      )}
    </Modal>
  );
}
