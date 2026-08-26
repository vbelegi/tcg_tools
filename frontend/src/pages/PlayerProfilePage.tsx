import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";

type HistoryRow = {
  event_id: number;
  event_name: string;
  event_date: string;
  source: string;
  rank: number | null;
  rank_label: string | null;
  is_drop: boolean;
  decklist: string | null;
};

export function PlayerProfilePage() {
  const { id = "" } = useParams();
  const userId = Number(id);
  const { data, isLoading, error } = useQuery({
    queryKey: ["profile", userId],
    queryFn: () => api.publicProfile(userId) as Promise<{
      display_name: string;
      fourse_points: number;
      history: HistoryRow[];
    }>,
    enabled: Number.isFinite(userId),
  });

  if (isLoading) return <p>Carregando...</p>;
  if (error) return <p className="error">{(error as Error).message}</p>;
  if (!data) return null;

  return (
    <div>
      <h1>{data.display_name}</h1>
      <p>
        <strong>{data.fourse_points}</strong> Fourse Points (FP)
      </p>
      <h2>Torneios</h2>
      {data.history.length === 0 && <p>Nenhum torneio finalizado vinculado.</p>}
      <ul className="participant-list">
        {data.history.map((h) => (
          <li key={`${h.event_id}-${h.rank_label}`}>
            <Link to={`/torneios/${h.event_id}/resultado`}>
              {h.event_name}
            </Link>{" "}
            ({h.event_date}) — {h.is_drop ? "DROP" : h.rank_label || "—"}
            {h.source === "external" ? " · externo" : ""}
            {h.decklist ? (
              <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem" }}>{h.decklist}</pre>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
