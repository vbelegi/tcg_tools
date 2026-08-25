import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";

export function AlterarSenhaPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  const change = useMutation({
    mutationFn: () => api.changePassword(currentPassword, newPassword),
    onSuccess: async (res) => {
      setOk(res.message);
      setError("");
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
      window.setTimeout(() => navigate("/login", { replace: true }), 800);
    },
    onError: (e) => {
      setOk("");
      setError((e as Error).message);
    },
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      setError("Nova senha deve ter pelo menos 6 caracteres.");
      return;
    }
    if (newPassword !== confirm) {
      setError("Confirmação não confere.");
      return;
    }
    change.mutate();
  };

  return (
    <div>
      <h1>Alterar senha</h1>
      <p style={{ opacity: 0.85 }}>Altera a senha do admin sem reinstalar o aplicativo.</p>
      {error && <p className="error">{error}</p>}
      {ok && <p className="success">{ok}</p>}
      <form onSubmit={onSubmit}>
        <div className="form-row">
          <label htmlFor="cur-pass">Senha atual</label>
          <input
            id="cur-pass"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            minLength={6}
          />
        </div>
        <div className="form-row">
          <label htmlFor="new-pass">Nova senha</label>
          <input
            id="new-pass"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={6}
          />
        </div>
        <div className="form-row">
          <label htmlFor="confirm-pass">Confirmar nova senha</label>
          <input
            id="confirm-pass"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
            minLength={6}
          />
        </div>
        <button className="primary" type="submit" disabled={change.isPending}>
          {change.isPending ? "Salvando…" : "Salvar nova senha"}
        </button>
      </form>
    </div>
  );
}
