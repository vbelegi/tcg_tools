import { Outlet } from "react-router-dom";

import { SiteFooter } from "./SiteFooter";

/** Shell for auth / token pages outside the main app Layout. */
export function AuthShell() {
  return (
    <div className="auth-shell">
      <div className="auth-shell-body">
        <Outlet />
      </div>
      <SiteFooter />
    </div>
  );
}
