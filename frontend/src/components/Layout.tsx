import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { safeRedirectPath } from "../utils/safeRedirect";
import { isAdminRole, isStaffRole } from "../utils/roles";
import { EmailVerificationBanner } from "./EmailVerificationBanner";
import { AuthModal, type AuthModalMode } from "./AuthModal";
import { SiteFooter } from "./SiteFooter";

export function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [params, setParams] = useSearchParams();
  const qc = useQueryClient();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
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

  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  const logout = useMutation({
    mutationFn: () => api.logout(),
    onSuccess: async () => {
      await qc.resetQueries({ queryKey: ["auth-me"] });
      navigate("/", { replace: true });
    },
  });

  const isStaff = me && isStaffRole(me.role);
  const isAdmin = me && isAdminRole(me.role);

  const fromState = useMemo(
    () => (location.state as { from?: string } | null)?.from,
    [location.state],
  );

  const accountActions = (
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
  );

  return (
    <div className={`app-shell${mobileNavOpen ? " mobile-nav-open" : ""}`}>
      <button
        type="button"
        className="mobile-nav-toggle"
        aria-label={mobileNavOpen ? "Fechar menu" : "Abrir menu"}
        aria-expanded={mobileNavOpen}
        onClick={() => setMobileNavOpen((open) => !open)}
      >
        <span />
        <span />
        <span />
      </button>
      {mobileNavOpen && (
        <button
          type="button"
          className="mobile-nav-backdrop"
          aria-label="Fechar menu"
          onClick={() => setMobileNavOpen(false)}
        />
      )}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1 className="brand-title">TCG Tools</h1>
        </div>
        {accountActions}
        <nav>
          <NavLink to="/" end>
            Início
          </NavLink>
          <NavLink to="/calendario">Calendário</NavLink>
          <NavLink to="/ranking">Ranking Fourse Points</NavLink>
          <NavLink to="/torneios">Torneios</NavLink>
          <NavLink to="/acoes">Ações Promocionais</NavLink>
          {isStaff && (
            <>
              <NavLink to="/agenda">Agenda</NavLink>
              <NavLink to="/premiacao">Premiação</NavLink>
              <NavLink to="/sorteador">Sorteador</NavLink>
            </>
          )}
          {isAdmin && (
            <>
              <NavLink to="/usuarios">Usuários</NavLink>
              <NavLink to="/auditoria">Logs</NavLink>
              <NavLink to="/tcgs">TCGs</NavLink>
            </>
          )}
        </nav>
      </aside>
      <div className="app-body">
        <main className="main-content">
          {me && me.status === "active" && me.email_verified === false && (
            <EmailVerificationBanner email={me.email} />
          )}
          <Outlet />
        </main>
        <SiteFooter />
      </div>
      <AuthModal
        open={authOpen && !me}
        mode={authMode}
        onModeChange={openAuth}
        onClose={closeAuth}
        nextPath={safeRedirectPath(nextPath || fromState || null)}
      />
    </div>
  );
}
