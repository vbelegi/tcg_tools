import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { api } from "../api/client";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const forgot = useMutation({
    mutationFn: () => api.forgotPassword(email),
    onSuccess: () => setSubmitted(true),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    forgot.mutate();
  };

  return (
    <div className="login-page">
      <h1>Esqueci minha senha</h1>
      {submitted ? (
        <p className="success">
          Se existir uma conta com esse e-mail, você receberá um link em breve.
        </p>
      ) : (
        <>
          <p>Informe o e-mail da sua conta. Enviaremos um link para redefinir a senha.</p>
          <form onSubmit={onSubmit} className="login-form">
            <div className="form-row">
              <label htmlFor="forgot-email">E-mail</label>
              <input
                id="forgot-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                autoFocus
              />
            </div>
            <button className="primary" type="submit" disabled={forgot.isPending || !email}>
              {forgot.isPending ? "Enviando…" : "Enviar link"}
            </button>
          </form>
          {forgot.isError && <p className="error">{(forgot.error as Error).message}</p>}
        </>
      )}
      <p style={{ marginTop: "1rem" }}>
        <Link to="/?auth=login">← Voltar ao login</Link>
      </p>
    </div>
  );
}
