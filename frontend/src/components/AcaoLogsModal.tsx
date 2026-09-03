import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { formatDateTime } from "../pages/acoes/promoFormat";
import { Modal } from "./Modal";

type Props = {
  open: boolean;
  actionId: number;
  onClose: () => void;
};

const ACTION_LABELS: Record<string, string> = {
  "promo.create": "Criou a ação",
  "promo.edit": "Editou a ação",
  "promo.publish": "Publicou a ação",
  "promo.regulation": "Atualizou o regulamento",
  "promo.enroll_token": "Gerou QR de inscrição",
};

function labelFor(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

export function AcaoLogsModal({ open, actionId, onClose }: Props) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["acao-logs", actionId],
    queryFn: () => api.listPromoLogs(actionId),
    enabled: open,
  });

  return (
    <Modal
      open={open}
      title="Logs da ação"
      onClose={onClose}
      footer={
        <button className="primary" type="button" onClick={onClose}>
          Fechar
        </button>
      }
    >
      {isLoading && <p>Carregando...</p>}
      {isError && <p className="error">{(error as Error).message}</p>}
      {data && data.length === 0 && <p className="muted">Nenhum registro ainda.</p>}
      {data && data.length > 0 && (
        <ul className="promo-log-list">
          {data.map((row) => (
            <li key={row.id}>
              <strong>{labelFor(row.action)}</strong>
              <p className="muted">
                {row.actor_display_name || "Sistema"}
                {row.created_at ? ` · ${formatDateTime(row.created_at)}` : ""}
              </p>
            </li>
          ))}
        </ul>
      )}
    </Modal>
  );
}
