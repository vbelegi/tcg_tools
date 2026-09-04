import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { isAdminRole, isStaffRole } from "../utils/roles";

function useAuthMe() {
  return useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
}

function loginRedirect(pathname: string, search: string) {
  const next = encodeURIComponent(pathname + search);
  return <Navigate to={`/?auth=login&next=${next}`} replace />;
}

export function RequireAuth() {
  const location = useLocation();
  const { data, isLoading, isError } = useAuthMe();

  if (isLoading) return <p>Carregando...</p>;
  if (isError || !data) {
    return loginRedirect(location.pathname, location.search);
  }
  return <Outlet />;
}

export function RequireStaff() {
  const location = useLocation();
  const { data, isLoading, isError } = useAuthMe();

  if (isLoading) return <p>Carregando...</p>;
  if (isError || !data) {
    return loginRedirect(location.pathname, location.search);
  }
  if (!isStaffRole(data.role)) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}

export function RequireAdmin() {
  const location = useLocation();
  const { data, isLoading, isError } = useAuthMe();

  if (isLoading) return <p>Carregando...</p>;
  if (isError || !data) {
    return loginRedirect(location.pathname, location.search);
  }
  if (!isAdminRole(data.role)) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
