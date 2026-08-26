import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const qc = useQueryClient();
  const [email, setEmail] = useState("admin@local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const { data: me, isLoading } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });

  const login = useMutation({
    mutationFn: () => api.login(email, password),
    onSuccess: async () => {
      setError("");
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
      const from = (location.state as { from?: string } | null)?.from || "/";
      navigate(from, { replace: true });
    },
    onError: (e) => setError((e as Error).message),
  });

  if (isLoading) return <p>Carregando...</p>;
  if (me) return <Navigate to="/" replace />;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    login.mutate();
  };

  return (
    <div className="login-page">
      <h1>TCG Tools</h1>
      <p style={{ opacity: 0.85 }}>Entre com e-mail e senha para continuar.</p>
      {error && <p className="error">{error}</p>}
      <form onSubmit={onSubmit} className="login-form">
        <div className="form-row">
          <label htmlFor="login-email">E-mail</label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="username"
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="login-pass">Senha</label>
          <input
            id="login-pass"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            autoFocus
            minLength={6}
            required
          />
        </div>
        <button className="primary" type="submit" disabled={login.isPending || password.length < 6}>
          {login.isPending ? "Entrando…" : "Entrar"}
        </button>
      </form>
      <p className="field-hint" style={{ marginTop: "1rem" }}>
        Admin padrão: admin@local (senha definida no instalador). Contas incompletas usam o link de
        convite.
      </p>
      <div className="login-powered">
        <a
          className="powered-by"
          href="https://fourse.com.br"
          target="_blank"
          rel="noopener noreferrer"
        >
          <span>Powered by</span>
          <span className="fourse-logo">FOURSE</span>
        </a>
      </div>
    </div>
  );
}
