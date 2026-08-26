import { useEffect, useMemo } from "react";
import { NavLink, Outlet, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { AuthModal, type AuthModalMode } from "./AuthModal";

export function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [params, setParams] = useSearchParams();
  const qc = useQueryClient();
  const { data: me } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });

  const authParam = params.get("auth");
  const authOpen = authParam === "login" || authParam === "register";
  const authMode: AuthModalMode = authParam === "register" ? "register" : "login";
  const nextPath = params.get("next");

  const closeAuth = () => {
    const next = new URLSearchParams(params);
    next.delete("auth");
    next.delete("next");
    setParams(next, { replace: true });
  };

  const openAuth = (mode: AuthModalMode) => {
    const next = new URLSearchParams(params);
    next.set("auth", mode);
    setParams(next, { replace: true });
  };

  useEffect(() => {
    if (me && authOpen) closeAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- close once when session appears
  }, [me]);

  const logout = useMutation({
    mutationFn: () => api.logout(),
    onSuccess: async () => {
      await qc.resetQueries({ queryKey: ["auth-me"] });
      navigate("/", { replace: true });
    },
  });

  const isStaff = me && (me.role === "admin" || me.role === "staff");
  const isAdmin = me?.role === "admin";

  const fromState = useMemo(
    () => (location.state as { from?: string } | null)?.from,
    [location.state],
  );

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
          <NavLink to="/calendario">Calendário</NavLink>
          <NavLink to="/ranking">Ranking Fourse Points</NavLink>
          <NavLink to="/torneios">Torneios</NavLink>
          {isStaff && (
            <>
              <NavLink to="/premiacao">Premiação</NavLink>
              <NavLink to="/sorteador">Sorteador</NavLink>
            </>
          )}
          {isAdmin && (
            <>
              <NavLink to="/usuarios">Usuários</NavLink>
              <NavLink to="/tcgs">TCGs</NavLink>
            </>
          )}
        </nav>
        <div className="sidebar-actions">
          {me ? (
            <>
              <NavLink to={`/jogadores/${me.id}`} className="secondary sidebar-profile-link">
                Meu Perfil
              </NavLink>
              <button
                className="secondary"
                type="button"
                style={{ width: "100%" }}
                onClick={() => logout.mutate()}
                disabled={logout.isPending}
              >
                Sair ({me.display_name})
              </button>
            </>
          ) : (
            <button
              className="primary"
              type="button"
              style={{ width: "100%" }}
              onClick={() => openAuth("login")}
            >
              Entrar
            </button>
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
      <AuthModal
        open={authOpen && !me}
        mode={authMode}
        onModeChange={openAuth}
        onClose={closeAuth}
        nextPath={nextPath || fromState || null}
      />
    </div>
  );
}
