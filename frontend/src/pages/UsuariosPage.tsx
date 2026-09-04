import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { ChangeRoleModal } from "../components/ChangeRoleModal";
import {
  AppRole,
  ROLE_LABELS,
  assignableRoles,
  canEditUserRole,
  creatableRoles,
  isSuperadminRole,
} from "../utils/roles";

function inviteAbsoluteUrl(claimPath: string, claimUrl?: string | null): string {
  if (claimUrl?.trim()) return claimUrl.trim();
  const path = claimPath.startsWith("/") ? claimPath : `/${claimPath}`;
  return `${window.location.origin}${path}`;
}

export function UsuariosPage() {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [role, setRole] = useState("player");
  const [inviteMsg, setInviteMsg] = useState("");
  const [error, setError] = useState("");
  const [roleTarget, setRoleTarget] = useState<{
    id: number;
    display_name: string;
    role: string;
  } | null>(null);
  const [roleModalError, setRoleModalError] = useState("");

  const { data = [], isLoading } = useQuery({
    queryKey: ["users", q],
    queryFn: () => api.listUsers(q || undefined),
  });

  const { data: me } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });

  const createRoleOptions = creatableRoles(me?.role);
  const changeRoleOptions = assignableRoles(me?.role);

  const roleChange = useMutation({
    mutationFn: ({
      id,
      role: nextRole,
      current_password,
    }: {
      id: number;
      role: AppRole;
      current_password: string;
    }) => api.updateUserRole(id, nextRole, current_password),
    onSuccess: async () => {
      setError("");
      setRoleModalError("");
      setRoleTarget(null);
      await qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (e) => setRoleModalError((e as Error).message),
  });

  const create = useMutation({
    mutationFn: () => api.createUser({ display_name: displayName, email, phone, role }),
    onSuccess: async () => {
      setDisplayName("");
      setEmail("");
      setPhone("");
      setError("");
      await qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const invite = useMutation({
    mutationFn: (id: number) => api.inviteUser(id),
    onSuccess: async (res) => {
      const url = inviteAbsoluteUrl(res.claim_path, res.claim_url);
      try {
        await navigator.clipboard.writeText(url);
        setInviteMsg(
          `Convite enviado por e-mail. Link também copiado (válido até ${res.expires_at}): ${url}`,
        );
      } catch {
        setInviteMsg(`Convite enviado por e-mail. Link (válido até ${res.expires_at}): ${url}`);
      }
    },
    onError: (e) => setError((e as Error).message),
  });

  const passwordReset = useMutation({
    mutationFn: (id: number) => api.resetUserPassword(id),
    onSuccess: async (res) => {
      setError("");
      const url = inviteAbsoluteUrl(res.reset_path, res.reset_url);
      try {
        await navigator.clipboard.writeText(url);
        setInviteMsg(
          `Link de redefinição copiado. Encaminhe ao usuário. Válido até ${res.expires_at}: ${url}`,
        );
      } catch {
        setInviteMsg(`Copie e encaminhe o link de redefinição (válido até ${res.expires_at}): ${url}`);
      }
    },
    onError: (e) => setError((e as Error).message),
  });

  const exportContacts = useMutation({
    mutationFn: () => api.exportContactsCsv(),
    onError: (e) => setError((e as Error).message),
    onSuccess: () => setInviteMsg("CSV de contatos baixado."),
  });

  const deleteUser = useMutation({
    mutationFn: (id: number) => api.deleteUser(id),
    onSuccess: async () => {
      setError("");
      await qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const onCreate = (e: FormEvent) => {
    e.preventDefault();
    create.mutate();
  };

  return (
    <div className="admin-page">
      <header className="torneio-manage-header">
        <div>
          <h1>Usuários</h1>
          <p className="torneio-manage-meta">
            Contas incomplete · convite manual · {data.length} listado(s)
          </p>
        </div>
        <div className="torneio-manage-primary">
          <button
            type="button"
            className="secondary"
            disabled={exportContacts.isPending}
            onClick={() => exportContacts.mutate()}
            title="Nome e telefone de contas ativas sem opt-out"
          >
            {exportContacts.isPending ? "Exportando…" : "Aptos a contato (CSV)"}
          </button>
        </div>
      </header>

      {error && <p className="error">{error}</p>}
      {inviteMsg && <p className="success">{inviteMsg}</p>}

      <details className="torneio-advanced admin-create-panel">
        <summary>Nova conta (incomplete)</summary>
        <form onSubmit={onCreate} className="admin-form-dense">
          <div className="admin-form-grid">
            <div className="form-row">
              <label>Nome de exibição</label>
              <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
            </div>
            <div className="form-row">
              <label>E-mail</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="form-row">
              <label>Celular</label>
              <input
                type="tel"
                inputMode="numeric"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                placeholder="11987654321"
                autoComplete="tel"
              />
              <p className="field-hint">DDD + número (10 a 13 dígitos), ex.: 11987654321</p>
            </div>
            <div className="form-row">
              <label>Papel</label>
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                {createRoleOptions.map((r) => (
                  <option key={r} value={r}>
                    {ROLE_LABELS[r] ?? r}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button className="primary" type="submit" disabled={create.isPending}>
            {create.isPending ? "Criando…" : "Criar"}
          </button>
        </form>
      </details>

      <section className="resultado-section">
        <div className="admin-inline-add">
          <div className="form-row admin-inline-add-field">
            <label htmlFor="users-search">Buscar</label>
            <input
              id="users-search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="nome, e-mail ou celular"
            />
          </div>
        </div>

        {isLoading && <p>Carregando...</p>}

        <div className="resultado-table-wrap">
          <table className="resultado-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>E-mail</th>
                <th>Celular</th>
                <th>Papel</th>
                <th>Status</th>
                <th className="admin-col-actions">Ações</th>
              </tr>
            </thead>
            <tbody>
              {data.map((u) => {
                const self = u.id === me?.id;
                const editable = canEditUserRole(me?.role, u.role, self);
                const canDelete =
                  !self &&
                  (isSuperadminRole(me?.role)
                    ? u.role !== "superadmin" || data.filter((x) => x.role === "superadmin").length > 1
                    : u.role !== "admin" && u.role !== "superadmin");
                return (
                  <tr key={u.id}>
                    <td className="resultado-player-cell">
                      <Link to={`/jogadores/${u.id}`}>{u.display_name}</Link>
                    </td>
                    <td>{u.email}</td>
                    <td>{u.phone}</td>
                    <td>
                      <span className="badge">{ROLE_LABELS[u.role] ?? u.role}</span>
                      {editable && (
                        <button
                          type="button"
                          className="secondary"
                          style={{ marginLeft: "0.5rem" }}
                          onClick={() => {
                            setRoleModalError("");
                            setRoleTarget({
                              id: u.id,
                              display_name: u.display_name,
                              role: u.role,
                            });
                          }}
                        >
                          Alterar
                        </button>
                      )}
                    </td>
                    <td>
                      <span className={u.status === "incomplete" ? "badge badge-warn" : "badge badge-ok"}>
                        {u.status}
                      </span>
                    </td>
                    <td className="admin-col-actions">
                      {u.status === "incomplete" && (
                        <button
                          className="secondary"
                          type="button"
                          onClick={() => invite.mutate(u.id)}
                        >
                          {invite.isPending ? "…" : "Convite"}
                        </button>
                      )}
                      {u.status === "active" && u.id !== me?.id && (
                        <button
                          className="secondary"
                          type="button"
                          onClick={() => {
                            if (
                              window.confirm(
                                `Gerar link de redefinição de senha para ${u.display_name}? Sessões ativas serão encerradas.`,
                              )
                            ) {
                              passwordReset.mutate(u.id);
                            }
                          }}
                          disabled={passwordReset.isPending}
                        >
                          Reset senha
                        </button>
                      )}
                      {canDelete && (
                        <button
                          className="secondary"
                          type="button"
                          onClick={() => {
                            if (
                              window.confirm(
                                `Excluir conta de ${u.display_name}? Histórico de torneios ficará como Anônimo.`,
                              )
                            ) {
                              deleteUser.mutate(u.id);
                            }
                          }}
                          disabled={deleteUser.isPending}
                        >
                          Excluir
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <ChangeRoleModal
        open={roleTarget != null}
        displayName={roleTarget?.display_name ?? ""}
        currentRole={roleTarget?.role ?? "player"}
        allowedRoles={changeRoleOptions}
        pending={roleChange.isPending}
        error={roleModalError}
        onClose={() => {
          if (!roleChange.isPending) {
            setRoleTarget(null);
            setRoleModalError("");
          }
        }}
        onConfirm={(nextRole, currentPassword) => {
          if (!roleTarget) return;
          roleChange.mutate({
            id: roleTarget.id,
            role: nextRole,
            current_password: currentPassword,
          });
        }}
      />
    </div>
  );
}
