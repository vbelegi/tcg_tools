import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

export function Home() {
  const { data: me } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const isStaff = me && (me.role === "admin" || me.role === "staff");

  return (
    <div>
      <h1>TCG Tools</h1>
      <p>Ferramentas para organização de torneios na loja Fourse.</p>
      <div className="card-grid" style={{ marginTop: "2rem" }}>
        <Link to="/torneios" className="card">
          <h2>Torneios</h2>
          <p>Eventos, resultados e inscrições.</p>
        </Link>
        <Link to="/ranking" className="card">
          <h2>Ranking FP</h2>
          <p>Fourse Points acumulados pelos jogadores.</p>
        </Link>
        {isStaff && (
          <>
            <Link to="/premiacao" className="card">
              <h2>Premiação</h2>
              <p>Calcular split de prêmios, tabelas e presets.</p>
            </Link>
            <Link to="/sorteador" className="card">
              <h2>Sorteador</h2>
              <p>Sortear prêmios entre participantes cadastrados.</p>
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
