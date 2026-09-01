import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";

export function VerificarEmailContaPage() {
  const resend = useMutation({
    mutationFn: () => api.resendVerification(),
  });

  return (
    <div className="admin-page">
      <h1>Verificar e-mail</h1>
      <p>
        Enviamos um link de confirmação para o e-mail da sua conta. O link é válido por 24 horas.
      </p>
      <p>
        Não recebeu? Clique abaixo para reenviar (máximo uma vez a cada 10 minutos).
      </p>
      <button
        type="button"
        className="primary"
        disabled={resend.isPending}
        onClick={() => resend.mutate()}
      >
        {resend.isPending ? "Enviando…" : "Reenviar e-mail de verificação"}
      </button>
      {resend.isSuccess && <p className="success">E-mail enviado. Verifique sua caixa de entrada.</p>}
      {resend.isError && <p className="error">{(resend.error as Error).message}</p>}
      <p style={{ marginTop: "1.5rem" }}>
        <Link to="/">← Voltar</Link>
      </p>
    </div>
  );
}
