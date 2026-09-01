import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";

export function VerifyEmailPage() {
  const { token = "" } = useParams();
  const navigate = useNavigate();

  const qc = useQueryClient();
  const verify = useMutation({
    mutationFn: () => api.verifyEmail(token),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
      setTimeout(() => navigate("/", { replace: true }), 2000);
    },
  });

  useEffect(() => {
    if (token) verify.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once per token
  }, [token]);

  if (verify.isPending) return <div className="login-page"><p>Verificando e-mail…</p></div>;
  if (verify.isError) {
    return (
      <div className="login-page">
        <h1>Verificação de e-mail</h1>
        <p className="error">{(verify.error as Error).message}</p>
        <p>
          <Link to="/conta/verificar-email">Reenviar link de verificação</Link>
        </p>
      </div>
    );
  }
  return (
    <div className="login-page">
      <h1>E-mail confirmado</h1>
      <p className="success">Sua conta foi verificada. Redirecionando…</p>
      <p>
        <Link to="/">Ir para o início</Link>
      </p>
    </div>
  );
}
