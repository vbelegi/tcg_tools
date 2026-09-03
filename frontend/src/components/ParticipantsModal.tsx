import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { Modal } from "./Modal";

type Props = {
  open: boolean;
  actionId: number;
  onClose: () => void;
};

function statusLabel(status: string): string {
  if (status === "confirmed") return "Confirmado";
  if (status === "pending_verification") return "Pendente (e-mail)";
  return status;
}

export function ParticipantsModal({ open, actionId, onClose }: Props) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["acao-participants", actionId],
    queryFn: () => api.listPromoParticipants(actionId),
    enabled: open,
  });

  return (
    <Modal
      open={open}
      title="Participantes"
      onClose={onClose}
      footer={
        <button className="primary" type="button" onClick={onClose}>
          Fechar
        </button>
      }
    >
      {isLoading && <p>Carregando...</p>}
      {isError && <p className="error">{(error as Error).message}</p>}
      {data && data.length === 0 && <p className="muted">Nenhum inscrito ainda.</p>}
      {data && data.length > 0 && (
        <ul className="promo-participants-list">
          {data.map((row) => (
            <li key={row.id}>
              <span>{row.display_name}</span>
              <span className="badge">{statusLabel(row.status)}</span>
            </li>
          ))}
        </ul>
      )}
    </Modal>
  );
}
