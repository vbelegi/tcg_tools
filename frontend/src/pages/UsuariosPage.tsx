import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

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

  const { data = [], isLoading } = useQuery({
    queryKey: ["users", q],
    queryFn: () => api.listUsers(q || undefined),
  });

  const { data: me } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });

  const roleChange = useMutation({
    mutationFn: ({ id, role }: { id: number; role: "staff" | "player" }) =>
      api.updateUserRole(id, role),
    onSuccess: async () => {
      setError("");
      await qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (e) => setError((e as Error).message),
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
              <input value={phone} onChange={(e) => setPhone(e.target.value)} required />
            </div>
            <div className="form-row">
              <label>Papel</label>
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="player">player</option>
                <option value="staff">staff</option>
                <option value="admin">admin</option>
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
              {data.map((u) => (
                <tr key={u.id}>
                  <td className="resultado-player-cell">
                    <Link to={`/jogadores/${u.id}`}>{u.display_name}</Link>
                  </td>
                  <td>{u.email}</td>
                  <td>{u.phone}</td>
                  <td>
                    {u.role === "admin" || u.id === me?.id ? (
                      <span className="badge">{u.role}</span>
                    ) : (
                      <select
                        className="role-select"
                        value={u.role === "staff" ? "staff" : "player"}
                        disabled={roleChange.isPending}
                        onChange={(e) =>
                          roleChange.mutate({
                            id: u.id,
                            role: e.target.value as "staff" | "player",
                          })
                        }
                        aria-label={`Papel de ${u.display_name}`}
                      >
                        <option value="player">player</option>
                        <option value="staff">staff</option>
                      </select>
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
