import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { resolveAvatarUrl } from "../utils/tcgIcons";

type RankingRow = {
  rank: number;
  user_id: number;
  display_name: string;
  points: number;
  avatar_url?: string | null;
};

function RankBadge({ rank }: { rank: number }) {
  const top = rank <= 3 ? ` ranking-rank-top-${rank}` : "";
  return <span className={`resultado-rank-badge${top}`}>{rank}</span>;
}

function PlayerCell({ row }: { row: RankingRow }) {
  return (
    <Link to={`/jogadores/${row.user_id}`} className="ranking-player-link">
      <img
        className="ranking-avatar"
        src={resolveAvatarUrl(row.avatar_url)}
        alt=""
        width={32}
        height={32}
      />
      <span className="ranking-player-name">{row.display_name}</span>
    </Link>
  );
}

export function RankingPage() {
  const { data = [], isLoading } = useQuery({
    queryKey: ["ranking"],
    queryFn: () => api.ranking(),
  });

  const rows = data as RankingRow[];
  const podium = rows.filter((r) => r.rank <= 3);
  const rest = rows.filter((r) => r.rank > 3);

  return (
    <div className="ranking-page">
      <header className="torneio-manage-header">
        <div>
          <h1>Ranking Fourse Points</h1>
          <p className="torneio-manage-meta">
            FP acumulados em torneios finalizados (internos e externos)
            {rows.length > 0 ? ` · ${rows.length} jogador(es)` : ""}
          </p>
        </div>
      </header>

      {isLoading && <p>Carregando...</p>}

      {!isLoading && rows.length === 0 && (
        <p className="field-hint">Ainda não há Fourse Points registrados.</p>
      )}

      {podium.length > 0 && (
        <section className="ranking-podium" aria-label="Top 3">
          {podium.map((row) => (
            <article
              key={row.user_id}
              className={`ranking-podium-card ranking-podium-${row.rank}`}
            >
              <RankBadge rank={row.rank} />
              <Link to={`/jogadores/${row.user_id}`} className="ranking-podium-player">
                <img
                  className="ranking-avatar ranking-avatar-lg"
                  src={resolveAvatarUrl(row.avatar_url)}
                  alt=""
                  width={48}
                  height={48}
                />
                <span className="ranking-player-name">{row.display_name}</span>
              </Link>
              <div className="ranking-podium-fp">
                <strong>{row.points}</strong>
                <span className="muted">FP</span>
              </div>
            </article>
          ))}
        </section>
      )}

      {rest.length > 0 && (
        <section className="resultado-section">
          <div className="resultado-table-wrap">
            <table className="resultado-table ranking-table">
              <thead>
                <tr>
                  <th className="resultado-rank-cell">#</th>
                  <th>Jogador</th>
                  <th>FP</th>
                </tr>
              </thead>
              <tbody>
                {rest.map((row) => (
                  <tr key={row.user_id}>
                    <td className="resultado-rank-cell">
                      <RankBadge rank={row.rank} />
                    </td>
                    <td>
                      <PlayerCell row={row} />
                    </td>
                    <td className="ranking-fp-cell">
                      <span className="ranking-fp-value">{row.points}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
