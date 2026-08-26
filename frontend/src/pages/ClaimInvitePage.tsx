import { FormEvent, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { api } from "../api/client";

export function ClaimInvitePage() {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [guardianName, setGuardianName] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [guardianRelation, setGuardianRelation] = useState("");
  const [error, setError] = useState("");

  const claim = useMutation({
    mutationFn: () =>
      api.claimInvite({
        token,
        password,
        birth_date: birthDate || undefined,
        guardian_name: guardianName || undefined,
        guardian_phone: guardianPhone || undefined,
        guardian_relation: guardianRelation || undefined,
      }),
    onSuccess: () => navigate("/", { replace: true }),
    onError: (e) => setError((e as Error).message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (password !== password2) {
      setError("Confirmação de senha não confere.");
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
          <label htmlFor="pw">Senha</label>
          <input
            id="pw"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={6}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="pw2">Confirmar senha</label>
          <input
            id="pw2"
            type="password"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            minLength={6}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="bd">Data de nascimento</label>
          <input id="bd" type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} />
        </div>
        <div className="form-row">
          <label htmlFor="gn">Responsável (se menor)</label>
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
        <button className="primary" type="submit" disabled={claim.isPending || password.length < 6}>
          {claim.isPending ? "Salvando…" : "Ativar conta"}
        </button>
      </form>
    </div>
  );
}
