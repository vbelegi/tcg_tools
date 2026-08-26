import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

export function RequireAuth() {
  const location = useLocation();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });

  if (isLoading) return <p>Carregando...</p>;
  if (isError || !data) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/?auth=login&next=${next}`} replace />;
  }
  return <Outlet />;
}
