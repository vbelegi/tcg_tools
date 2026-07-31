import { NavLink, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>TCG Tools</h1>
        <nav>
          <NavLink to="/" end>
            Início
          </NavLink>
          <NavLink to="/premiacao">Premiação</NavLink>
          <NavLink to="/torneios">Torneios</NavLink>
          <NavLink to="/sorteador">Sorteador</NavLink>
        </nav>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
