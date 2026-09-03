import { FormEvent, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { SiteFooter } from "../components/SiteFooter";

export function ClaimInvitePage() {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const passwordRef = useRef<HTMLInputElement>(null);
  const password2Ref = useRef<HTMLInputElement>(null);
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [guardianName, setGuardianName] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [guardianRelation, setGuardianRelation] = useState("");
  const [error, setError] = useState("");
  const [passwordInvalid, setPasswordInvalid] = useState(false);
  const [password2Invalid, setPassword2Invalid] = useState(false);
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);

  const { data: authStatus } = useQuery({
    queryKey: ["auth-status"],
    queryFn: () => api.authStatus(),
    staleTime: 60_000,
  });
  const minPasswordLen = authStatus?.min_password_length ?? 10;

  const claim = useMutation({
    mutationFn: () =>
      api.claimInvite({
        token,
        password,
        birth_date: birthDate,
        guardian_name: guardianName || undefined,
        guardian_phone: guardianPhone || undefined,
        guardian_relation: guardianRelation || undefined,
        accept_privacy: acceptPrivacy,
      }),
    onSuccess: () => navigate("/", { replace: true }),
    onError: (e) => setError((e as Error).message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setPasswordInvalid(false);
    setPassword2Invalid(false);
    if (!birthDate) {
      setError("Data de nascimento é obrigatória.");
      return;
    }
    if (!acceptPrivacy) {
      setError("Aceite os Termos de uso e a Política de privacidade.");
      return;
    }
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
      <h1>Finalizar cadastro</h1>
      <p>Defina sua senha para ativar a conta Fourse / TCG Tools.</p>
      {error && <p className="error">{error}</p>}
      <form onSubmit={onSubmit} className="login-form">
        <div className="form-row">
          <div className="form-label-row">
            <label htmlFor="pw">Senha</label>
            <span className="form-hint">mín. {minPasswordLen} caracteres</span>
          </div>
          <input
            id="pw"
            ref={passwordRef}
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setPasswordInvalid(false);
            }}
            required
            className={passwordInvalid ? "input-invalid" : undefined}
          />
        </div>
        <div className="form-row">
          <label htmlFor="pw2">Confirmar senha</label>
          <input
            id="pw2"
            ref={password2Ref}
            type="password"
            value={password2}
            onChange={(e) => {
              setPassword2(e.target.value);
              setPassword2Invalid(false);
            }}
            required
            className={password2Invalid ? "input-invalid" : undefined}
          />
        </div>
        <div className="form-row">
          <label htmlFor="bd">Data de nascimento</label>
          <input
            id="bd"
            type="date"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="gn">Responsável (obrigatório se menor de 18)</label>
          <input id="gn" value={guardianName} onChange={(e) => setGuardianName(e.target.value)} />
        </div>
        <div className="form-row">
          <label htmlFor="gp">Celular do responsável</label>
          <input id="gp" value={guardianPhone} onChange={(e) => setGuardianPhone(e.target.value)} />
        </div>
        <div className="form-row">
          <label htmlFor="gr">Parentesco</label>
          <input
            id="gr"
            value={guardianRelation}
            onChange={(e) => setGuardianRelation(e.target.value)}
          />
        </div>
        <label className="auth-privacy-check">
          <input
            type="checkbox"
            checked={acceptPrivacy}
            onChange={(e) => setAcceptPrivacy(e.target.checked)}
            required
          />
          <span>
            Li e aceito os <Link to="/termos">Termos de uso</Link> e a{" "}
            <Link to="/privacidade">Política de privacidade</Link>
          </span>
        </label>
        <button className="primary" type="submit" disabled={claim.isPending || !password}>
          {claim.isPending ? "Salvando…" : "Ativar conta"}
        </button>
      </form>
      <SiteFooter />
    </div>
  );
}
