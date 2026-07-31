import { useEffect, useState } from "react";

import { Modal } from "./Modal";

export type PlayerOption = { id: number; name: string };

type PlayerPickerModalProps = {
  open: boolean;
  title: string;
  description: string;
  players: PlayerOption[];
  confirmLabel?: string;
  pending?: boolean;
  onConfirm: (playerId: number) => void;
  onClose: () => void;
};

export function PlayerPickerModal({
  open,
  title,
  description,
  players,
  confirmLabel = "Confirmar",
  pending = false,
  onConfirm,
  onClose,
}: PlayerPickerModalProps) {
  const [selectedId, setSelectedId] = useState<string>("");

  useEffect(() => {
    if (open) setSelectedId(players.length === 1 ? String(players[0].id) : "");
  }, [open, players]);

  const handleConfirm = () => {
    if (!selectedId) return;
    onConfirm(Number(selectedId));
  };

  return (
    <Modal
      open={open}
      title={title}
      onClose={onClose}
      footer={
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
      }
    >
      <p className="modal-message">{description}</p>
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
    </Modal>
  );
}
