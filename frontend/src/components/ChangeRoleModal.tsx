import { FormEvent, useEffect, useState } from "react";

import { Modal } from "./Modal";
import { AppRole, ROLE_LABELS } from "../utils/roles";

type ChangeRoleModalProps = {
  open: boolean;
  displayName: string;
  currentRole: string;
  allowedRoles: AppRole[];
  pending?: boolean;
  error?: string;
  onConfirm: (role: AppRole, currentPassword: string) => void;
  onClose: () => void;
};

export function ChangeRoleModal({
  open,
  displayName,
  currentRole,
  allowedRoles,
  pending = false,
  error = "",
  onConfirm,
  onClose,
}: ChangeRoleModalProps) {
  const [role, setRole] = useState<AppRole>(
    (allowedRoles.includes(currentRole as AppRole) ? currentRole : allowedRoles[0]) as AppRole,
  );
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (!open) return;
    const initial = allowedRoles.includes(currentRole as AppRole)
      ? (currentRole as AppRole)
      : allowedRoles[0];
    setRole(initial);
    setPassword("");
  }, [open, currentRole, allowedRoles]);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    onConfirm(role, password);
  };

  return (
    <Modal
      open={open}
      title="Alterar papel"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="secondary" onClick={onClose} disabled={pending}>
            Cancelar
          </button>
          <button
            type="submit"
            form="change-role-form"
            className="primary"
            disabled={pending || !password || !role}
          >
            {pending ? "Confirmando…" : "Confirmar alteração"}
          </button>
        </>
      }
    >
      <p className="modal-message">
        Alterar o papel de <strong>{displayName}</strong> (atual:{" "}
        {ROLE_LABELS[currentRole] ?? currentRole}). Confirme com sua senha.
      </p>
      {error ? <p className="error">{error}</p> : null}
      <form id="change-role-form" onSubmit={onSubmit}>
        <div className="form-row">
          <label htmlFor="change-role-select">Novo papel</label>
          <select
            id="change-role-select"
            value={role}
            onChange={(e) => setRole(e.target.value as AppRole)}
            required
          >
            {allowedRoles.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r] ?? r}
              </option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="change-role-password">Sua senha</label>
          <input
            id="change-role-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>
      </form>
    </Modal>
  );
}
