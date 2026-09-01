import { FormEvent, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

export function ResetPasswordPage() {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const passwordRef = useRef<HTMLInputElement>(null);
  const password2Ref = useRef<HTMLInputElement>(null);
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [error, setError] = useState("");
  const [passwordInvalid, setPasswordInvalid] = useState(false);
  const [password2Invalid, setPassword2Invalid] = useState(false);

  const { data: authStatus } = useQuery({
    queryKey: ["auth-status"],
    queryFn: () => api.authStatus(),
    staleTime: 60_000,
  });
  const minPasswordLen = authStatus?.min_password_length ?? 10;

  const claim = useMutation({
    mutationFn: () => api.claimPasswordReset(token, password),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
      navigate("/", { replace: true });
    },
    onError: (e) => setError((e as Error).message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setPasswordInvalid(false);
    setPassword2Invalid(false);
    if (password.length < minPasswordLen) {
      setError(`Senha deve ter pelo menos ${minPasswordLen} caracteres.`);
      setPasswordInvalid(true);
      passwordRef.current?.focus();
      return;
    }
    if (password !== password2) {
      setError("Confirmação de senha não confere.");
      setPassword2Invalid(true);
      password2Ref.current?.focus();
      return;
    }
    claim.mutate();
  };

  return (
    <div className="login-page">
      <h1>Redefinir senha</h1>
      <p>Defina uma nova senha para sua conta.</p>
      {error && <p className="error">{error}</p>}
      <form onSubmit={onSubmit} className="login-form">
        <div className="form-row">
          <div className="form-label-row">
            <label htmlFor="reset-pw">Nova senha</label>
            <span className="form-hint">mín. {minPasswordLen} caracteres</span>
          </div>
          <input
            id="reset-pw"
            ref={passwordRef}
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setPasswordInvalid(false);
            }}
            required
            className={passwordInvalid ? "input-invalid" : undefined}
            autoComplete="new-password"
            autoFocus
          />
        </div>
        <div className="form-row">
          <label htmlFor="reset-pw2">Confirmar senha</label>
          <input
            id="reset-pw2"
            ref={password2Ref}
            type="password"
            value={password2}
            onChange={(e) => {
              setPassword2(e.target.value);
              setPassword2Invalid(false);
            }}
            required
            className={password2Invalid ? "input-invalid" : undefined}
            autoComplete="new-password"
          />
        </div>
        <button className="primary" type="submit" disabled={claim.isPending || !password}>
          {claim.isPending ? "Salvando…" : "Salvar senha"}
        </button>
      </form>
    </div>
  );
}
