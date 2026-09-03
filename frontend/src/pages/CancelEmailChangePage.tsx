import { useMutation } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";

export function CancelEmailChangePage() {
  const { token = "" } = useParams();

  const cancel = useMutation({
    mutationFn: () => api.cancelEmailChangeByToken(token),
  });

  useEffect(() => {
    if (token) cancel.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once per token
  }, [token]);

  if (cancel.isPending) {
    return (
      <div className="login-page">
        <p>Cancelando troca de e-mail…</p>
      </div>
    );
  }
  if (cancel.isError) {
    return (
      <div className="login-page">
        <h1>Troca de e-mail</h1>
        <p className="error">{(cancel.error as Error).message}</p>
        <p>
          <Link to="/">Ir para o início</Link>
        </p>
      </div>
    );
  }
  return (
    <div className="login-page">
      <h1>Troca cancelada</h1>
      <p className="success">O pedido de troca de e-mail foi cancelado. Seu e-mail atual permanece o mesmo.</p>
      <p>
        <Link to="/">Ir para o início</Link>
      </p>
    </div>
  );
}
