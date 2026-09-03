import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import type { PromoDrawResult } from "../api/types";

type Props = {
  actionId: number;
  initial?: PromoDrawResult | null;
};

export function PromoWinnersPanel({ actionId, initial = null }: Props) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["acao-winners", actionId],
    queryFn: () => api.listPromoWinners(actionId),
    initialData: initial ?? undefined,
  });

  const exportCsv = async () => {
    await api.exportPromoWinnersCsv(actionId);
  };

  return (
    <section className="promo-winners">
      <h2>Contemplados</h2>
      {isLoading && !data && <p>Carregando...</p>}
      {isError && <p className="error">{(error as Error).message}</p>}
      {data && (
        <>
          <ol className="raffle-winners">
            {data.winners.map((row, i) => (
              <li key={row.user_id}>
                <span className="raffle-winners-rank">Sorteado {i + 1}</span>
                <span className="raffle-winners-name">{row.display_name}</span>
              </li>
            ))}
          </ol>
          <button className="secondary" type="button" onClick={() => void exportCsv()}>
            Exportar CSV
          </button>
        </>
      )}
    </section>
  );
}
