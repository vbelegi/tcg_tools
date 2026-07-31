import { Link } from "react-router-dom";

export function Home() {
  return (
    <div>
      <h1>TCG Tools</h1>
      <p>Ferramentas para organização de torneios na loja.</p>
      <div className="card-grid" style={{ marginTop: "2rem" }}>
        <Link to="/premiacao" className="card">
          <h2>Premiação</h2>
          <p>Calcular split de prêmios, tabelas e presets.</p>
        </Link>
        <Link to="/torneios" className="card">
          <h2>Torneios</h2>
          <p>Organizar eventos Suíço ou Eliminatória.</p>
        </Link>
        <Link to="/sorteador" className="card">
          <h2>Sorteador</h2>
          <p>Sortear prêmios entre participantes cadastrados.</p>
        </Link>
      </div>
    </div>
  );
}
