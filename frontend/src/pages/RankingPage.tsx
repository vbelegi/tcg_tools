import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";

export function RankingPage() {
  const { data = [], isLoading } = useQuery({
    queryKey: ["ranking"],
    queryFn: () => api.ranking(),
  });

  return (
    <div>
      <h1>Ranking Fourse Points</h1>
      <p>FP acumulados em torneios finalizados (internos e externos).</p>
      {isLoading && <p>Carregando...</p>}
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Jogador</th>
            <th>FP</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.user_id}>
              <td>{row.rank}</td>
              <td>
                <Link to={`/jogadores/${row.user_id}`}>{row.display_name}</Link>
              </td>
              <td>{row.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
