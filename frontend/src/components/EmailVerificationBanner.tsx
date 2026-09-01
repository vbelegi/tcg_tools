import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";

type EmailVerificationBannerProps = {
  email: string;
};

export function EmailVerificationBanner({ email }: EmailVerificationBannerProps) {
  const qc = useQueryClient();
  const resend = useMutation({
    mutationFn: () => api.resendVerification(),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
    },
  });

  return (
    <div className="email-verify-banner" role="status">
      <p>
        <strong>Confirme seu e-mail</strong> ({email}) — verifique sua caixa de entrada ou{" "}
        <Link to="/conta/verificar-email">reenvie o link</Link>.
        {" "}
        <button
          type="button"
          className="email-verify-banner-btn"
          disabled={resend.isPending}
          onClick={() => resend.mutate()}
        >
          {resend.isPending ? "Enviando…" : "Reenviar agora"}
        </button>
      </p>
      {resend.isSuccess && <p className="email-verify-banner-msg">E-mail enviado.</p>}
      {resend.isError && (
        <p className="email-verify-banner-msg error">{(resend.error as Error).message}</p>
      )}
    </div>
  );
}
