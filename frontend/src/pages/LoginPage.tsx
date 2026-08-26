import { Navigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

/** Legacy /login URL → home with auth modal. */
export function LoginPage() {
  const [params] = useSearchParams();
  const { data: me, isLoading } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });

  if (isLoading) return <p>Carregando...</p>;
  if (me) return <Navigate to="/" replace />;

  const next = params.get("next");
  const q = new URLSearchParams();
  q.set("auth", "login");
  if (next) q.set("next", next);
  return <Navigate to={`/?${q.toString()}`} replace />;
}
