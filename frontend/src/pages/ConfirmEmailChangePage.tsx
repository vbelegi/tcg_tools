import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";

export function ConfirmEmailChangePage() {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const confirm = useMutation({
    mutationFn: () => api.confirmEmailChange(token),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
      setTimeout(() => navigate("/", { replace: true }), 2000);
    },
  });

  useEffect(() => {
    if (token) confirm.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once per token
  }, [token]);

  if (confirm.isPending) {
    return (
      <div className="login-page">
        <p>Confirmando novo e-mail…</p>
      </div>
    );
  }
  if (confirm.isError) {
    return (
      <div className="login-page">
        <h1>Troca de e-mail</h1>
        <p className="error">{(confirm.error as Error).message}</p>
        <p>
          <Link to="/">Ir para o início</Link>
        </p>
      </div>
    );
  }
  return (
    <div className="login-page">
      <h1>E-mail atualizado</h1>
      <p className="success">Seu novo e-mail foi confirmado. Redirecionando…</p>
      <p>
        <Link to="/">Ir para o início</Link>
      </p>
    </div>
  );
}
