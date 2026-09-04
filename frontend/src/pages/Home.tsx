import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { isAdminRole, isStaffRole } from "../utils/roles";
import { resolveAvatarUrl } from "../utils/tcgIcons";

type HomeLink = {
  to: string;
  title: string;
  hint: string;
  primary?: boolean;
};

export function Home() {
  const { data: me, isFetched } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const isStaff = Boolean(me && isStaffRole(me.role));
  const isAdmin = me && isAdminRole(me.role);

  const { data: ranking = [] } = useQuery({
    queryKey: ["ranking", "home"],
    queryFn: () => api.ranking(),
  });
  const podium = ranking.slice(0, 3);

  const publicLinks: HomeLink[] = [
    { to: "/calendario", title: "Calendário", hint: "Agenda mensal de eventos" },
    { to: "/torneios", title: "Torneios", hint: "Eventos, resultados e inscrições" },
    {
      to: "/acoes",
      title: "Ações Promocionais",
      hint: "Sorteios e ações da loja",
    },
    {
      to: "/ranking",
      title: "Ranking Fourse Points",
      hint: "Pontos acumulados pelos jogadores",
    },
  ];

  const staffLinks: HomeLink[] = [
    { to: "/torneios/novo", title: "Novo torneio", hint: "Criar draft interno", primary: true },
    { to: "/premiacao", title: "Premiação", hint: "Split, tabelas e presets" },
    { to: "/sorteador", title: "Sorteador", hint: "Sorteio batch ou encadeado" },
  ];

  const adminLinks: HomeLink[] = [
    { to: "/torneios/externo", title: "Importar externo", hint: "Resultados para FP" },
    { to: "/usuarios", title: "Usuários", hint: "Contas e convites" },
    { to: "/tcgs", title: "TCGs", hint: "Catálogo e cores" },
  ];

  return (
    <div className="home-page">
      <header className="torneio-manage-header">
        <div>
          <h1>TCG Tools</h1>
          <p className="torneio-manage-meta">Torneios e Fourse Points na loja Fourse</p>
        </div>
        <div className="torneio-manage-primary">
          {isFetched && !me && (
            <Link className="primary" to="/?auth=login">
              Entrar
            </Link>
          )}
          {me && (
            <Link className="secondary" to={`/jogadores/${me.id}`}>
              Meu Perfil
            </Link>
          )}
        </div>
      </header>

      <section className="resultado-section">
        <h2>Atalhos</h2>
        <ul className="home-link-list">
          {publicLinks.map((l) => (
            <li key={l.to}>
              <Link to={l.to} className="home-link-row">
                <span className="home-link-title">{l.title}</span>
                <span className="home-link-hint">{l.hint}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {isStaff && (
        <section className="resultado-section">
          <h2>Operação</h2>
          <ul className="home-link-list">
            {staffLinks.map((l) => (
              <li key={l.to}>
                <Link to={l.to} className={`home-link-row${l.primary ? " home-link-primary" : ""}`}>
                  <span className="home-link-title">{l.title}</span>
                  <span className="home-link-hint">{l.hint}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {isAdmin && (
        <section className="resultado-section">
          <h2>Admin</h2>
          <ul className="home-link-list">
            {adminLinks.map((l) => (
              <li key={l.to}>
                <Link to={l.to} className="home-link-row">
                  <span className="home-link-title">{l.title}</span>
                  <span className="home-link-hint">{l.hint}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {podium.length > 0 && (
        <section className="resultado-section">
          <div className="resultado-section-head">
            <h2>Top Ranking</h2>
            <Link to="/ranking" className="secondary">
              Ver ranking
            </Link>
          </div>
          <div className="home-podium">
            {podium.map((row) => (
              <Link
                key={row.user_id}
                to={`/jogadores/${row.user_id}`}
                className={`home-podium-card ranking-podium-${row.rank}`}
              >
                <span className={`resultado-rank-badge ranking-rank-top-${row.rank}`}>
                  {row.rank}
                </span>
                <img
                  className="ranking-avatar"
                  src={resolveAvatarUrl(row.avatar_url)}
                  alt=""
                  width={32}
                  height={32}
                />
                <span className="home-podium-name">{row.display_name}</span>
                <strong className="home-podium-fp">{row.points} FP</strong>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
