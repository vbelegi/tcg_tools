import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

export function Layout() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: me } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });

  const logout = useMutation({
    mutationFn: () => api.logout(),
    onSuccess: async () => {
      await qc.resetQueries({ queryKey: ["auth-me"] });
      navigate("/login", { replace: true });
    },
  });

  const isStaff = me && (me.role === "admin" || me.role === "staff");
  const isAdmin = me?.role === "admin";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1 className="brand-title">TCG Tools</h1>
        </div>
        <nav>
          <NavLink to="/" end>
            Início
          </NavLink>
          <NavLink to="/ranking">Ranking FP</NavLink>
          <NavLink to="/torneios">Torneios</NavLink>
          {isStaff && (
            <>
              <NavLink to="/premiacao">Premiação</NavLink>
              <NavLink to="/sorteador">Sorteador</NavLink>
            </>
          )}
          {isAdmin && <NavLink to="/usuarios">Usuários</NavLink>}
          {me && <NavLink to="/conta/senha">Alterar senha</NavLink>}
        </nav>
        <div className="sidebar-actions">
          {me ? (
            <button
              className="secondary"
              type="button"
              style={{ width: "100%" }}
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
            >
              Sair ({me.display_name})
            </button>
          ) : (
            <NavLink to="/login" className="primary" style={{ display: "block", textAlign: "center" }}>
              Entrar
            </NavLink>
          )}
        </div>
        <footer className="sidebar-footer">
          <a
            className="powered-by"
            href="https://fourse.com.br"
            target="_blank"
            rel="noopener noreferrer"
          >
            <span>Powered by</span>
            <span className="fourse-logo">FOURSE</span>
          </a>
        </footer>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
