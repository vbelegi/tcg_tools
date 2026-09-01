import { FormEvent, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, Link } from "react-router-dom";

import { api } from "../api/client";
import { safeRedirectPath } from "../utils/safeRedirect";
import { Modal } from "./Modal";

export type AuthModalMode = "login" | "register";

type AuthModalProps = {
  open: boolean;
  mode: AuthModalMode;
  onModeChange: (mode: AuthModalMode) => void;
  onClose: () => void;
  nextPath?: string | null;
};

export function AuthModal({ open, mode, onModeChange, onClose, nextPath }: AuthModalProps) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const passwordRef = useRef<HTMLInputElement>(null);
  const password2Ref = useRef<HTMLInputElement>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [phone, setPhone] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [guardianName, setGuardianName] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [guardianRelation, setGuardianRelation] = useState("");
  const [error, setError] = useState("");
  const [passwordInvalid, setPasswordInvalid] = useState(false);
  const [password2Invalid, setPassword2Invalid] = useState(false);

  useEffect(() => {
    if (!open) return;
    setError("");
    setPassword("");
    setPassword2("");
    setPasswordInvalid(false);
    setPassword2Invalid(false);
  }, [open, mode]);

  const { data: authStatus } = useQuery({
    queryKey: ["auth-status"],
    queryFn: () => api.authStatus(),
    staleTime: 60_000,
  });
  const minPasswordLen = authStatus?.min_password_length ?? 10;

  const afterAuth = async () => {
    setError("");
    await qc.invalidateQueries({ queryKey: ["auth-me"] });
    onClose();
    const target = safeRedirectPath(nextPath);
    if (target) navigate(target, { replace: true });
  };

  const login = useMutation({
    mutationFn: () => api.login(email, password),
    onSuccess: () => afterAuth(),
    onError: (e) => setError((e as Error).message),
  });

  const register = useMutation({
    mutationFn: () =>
      api.register({
        display_name: displayName,
        email,
        phone,
        password,
        birth_date: birthDate,
        guardian_name: guardianName || undefined,
        guardian_phone: guardianPhone || undefined,
        guardian_relation: guardianRelation || undefined,
      }),
    onSuccess: () => afterAuth(),
    onError: (e) => setError((e as Error).message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setPasswordInvalid(false);
    setPassword2Invalid(false);

    if (mode === "register") {
      if (!birthDate) {
        setError("Data de nascimento é obrigatória.");
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
      register.mutate();
      return;
    }
    login.mutate();
  };

  const pending = login.isPending || register.isPending;
  const title = mode === "login" ? "Entrar" : "Criar conta";
  const canSubmit =
    !pending &&
    password.length > 0 &&
    (mode === "login" || (Boolean(displayName.trim()) && Boolean(birthDate) && Boolean(phone.trim())));

  return (
    <Modal
      open={open}
      title={title}
      onClose={onClose}
      footer={
        <>
          <button className="secondary" type="button" onClick={onClose} disabled={pending}>
            Cancelar
          </button>
          <button className="primary" type="submit" form="auth-modal-form" disabled={!canSubmit}>
            {pending ? "Aguarde…" : mode === "login" ? "Entrar" : "Criar conta"}
          </button>
        </>
      }
    >
      <div className="auth-mode-tabs">
        <button
          type="button"
          className={mode === "login" ? "primary" : "secondary"}
          onClick={() => onModeChange("login")}
        >
          Entrar
        </button>
        <button
          type="button"
          className={mode === "register" ? "primary" : "secondary"}
          onClick={() => onModeChange("register")}
        >
          Criar conta
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      <form id="auth-modal-form" onSubmit={onSubmit}>
        {mode === "register" && (
          <>
            <div className="form-row">
              <label htmlFor="auth-name">Nome de exibição</label>
              <input
                id="auth-name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                autoComplete="nickname"
              />
            </div>
            <div className="form-row">
              <label htmlFor="auth-phone">Celular</label>
              <input
                id="auth-phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                autoComplete="tel"
              />
            </div>
            <div className="form-row">
              <label htmlFor="auth-bd">Data de nascimento</label>
              <input
                id="auth-bd"
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                required
              />
            </div>
            <div className="form-row">
              <label htmlFor="auth-gn">Responsável (obrigatório se menor de 18)</label>
              <input
                id="auth-gn"
                value={guardianName}
                onChange={(e) => setGuardianName(e.target.value)}
              />
            </div>
            <div className="form-row">
              <label htmlFor="auth-gp">Celular do responsável</label>
              <input
                id="auth-gp"
                value={guardianPhone}
                onChange={(e) => setGuardianPhone(e.target.value)}
              />
            </div>
            <div className="form-row">
              <label htmlFor="auth-gr">Parentesco</label>
              <input
                id="auth-gr"
                value={guardianRelation}
                onChange={(e) => setGuardianRelation(e.target.value)}
              />
            </div>
          </>
        )}
        <div className="form-row">
          <label htmlFor="auth-email">E-mail</label>
          <input
            id="auth-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="username"
          />
        </div>
        <div className="form-row">
          <div className="form-label-row">
            <label htmlFor="auth-pass">Senha</label>
            {mode === "register" && (
              <span className="form-hint">mín. {minPasswordLen} caracteres</span>
            )}
          </div>
          <input
            id="auth-pass"
            ref={passwordRef}
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setPasswordInvalid(false);
            }}
            required
            className={passwordInvalid ? "input-invalid" : undefined}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            autoFocus
          />
        </div>
        {mode === "login" && (
          <p className="auth-forgot-link">
            <Link to="/esqueci-senha" onClick={onClose}>
              Esqueci minha senha
            </Link>
          </p>
        )}
        {mode === "register" && (
          <div className="form-row">
            <label htmlFor="auth-pass2">Confirmar senha</label>
            <input
              id="auth-pass2"
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
        )}
      </form>
    </Modal>
  );
}
