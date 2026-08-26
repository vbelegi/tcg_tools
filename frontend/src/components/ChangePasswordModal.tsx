import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { Modal } from "./Modal";

type ChangePasswordModalProps = {
  open: boolean;
  onClose: () => void;
};

export function ChangePasswordModal({ open, onClose }: ChangePasswordModalProps) {
  const qc = useQueryClient();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  useEffect(() => {
    if (!open) return;
    setCurrentPassword("");
    setNewPassword("");
    setConfirm("");
    setError("");
    setOk("");
  }, [open]);

  const change = useMutation({
    mutationFn: () => api.changePassword(currentPassword, newPassword),
    onSuccess: async (res) => {
      setOk(res.message);
      setError("");
      await qc.invalidateQueries({ queryKey: ["auth-me"] });
      window.setTimeout(() => onClose(), 700);
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
    <Modal
      open={open}
      title="Alterar senha"
      onClose={onClose}
      footer={
        <button
          className="primary"
          type="submit"
          form="change-password-form"
          disabled={change.isPending}
        >
          {change.isPending ? "Salvando…" : "Salvar nova senha"}
        </button>
      }
    >
      {error && <p className="error">{error}</p>}
      {ok && <p className="success">{ok}</p>}
      <form id="change-password-form" onSubmit={onSubmit}>
        <div className="form-row">
          <label htmlFor="cur-pass">Senha atual</label>
          <input
            id="cur-pass"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            minLength={6}
            autoComplete="current-password"
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
            autoComplete="new-password"
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
            autoComplete="new-password"
          />
        </div>
      </form>
    </Modal>
  );
}
