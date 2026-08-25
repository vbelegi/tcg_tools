import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

export function Layout() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const logout = useMutation({
    mutationFn: () => api.logout(),
    onSuccess: async () => {
      await qc.resetQueries({ queryKey: ["auth-me"] });
      navigate("/login", { replace: true });
    },
  });

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
          <NavLink to="/premiacao">Premiação</NavLink>
          <NavLink to="/torneios">Torneios</NavLink>
          <NavLink to="/sorteador">Sorteador</NavLink>
          <NavLink to="/conta/senha">Alterar senha</NavLink>
        </nav>
        <div className="sidebar-actions">
          <button
            className="secondary"
            type="button"
            style={{ width: "100%" }}
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
          >
            Sair
          </button>
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
