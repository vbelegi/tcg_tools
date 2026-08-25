import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../api/client";

export function TorneiosListPage() {
  const { data, isLoading } = useQuery({ queryKey: ["torneios"], queryFn: api.listTorneios });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Torneios</h1>
        <Link to="/torneios/novo" className="primary">
          Novo torneio
        </Link>
      </div>
      {isLoading && <p>Carregando...</p>}
      {data && data.length === 0 && <p>Nenhum torneio cadastrado.</p>}
      <div className="card-grid" style={{ marginTop: "1rem" }}>
        {data?.map((t) => (
          <Link key={t.id} to={`/torneios/${t.id}`} className="card">
            <h2>{t.name}</h2>
            <p>{t.event_date} — <span className="badge">{t.status}</span></p>
            <p>{t.format === "swiss" ? "Suíço" : "Eliminatória"} · {t.player_count} jogadores</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
