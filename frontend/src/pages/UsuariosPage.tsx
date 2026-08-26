import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

function inviteAbsoluteUrl(claimPath: string): string {
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
      const url = inviteAbsoluteUrl(res.claim_path);
      try {
        await navigator.clipboard.writeText(url);
        setInviteMsg(
          `Link copiado. Encaminhe manualmente (WhatsApp/e-mail). Válido até ${res.expires_at}: ${url}`,
        );
      } catch {
        setInviteMsg(`Copie e encaminhe o link (válido até ${res.expires_at}): ${url}`);
      }
    },
    onError: (e) => setError((e as Error).message),
  });

  const onCreate = (e: FormEvent) => {
    e.preventDefault();
    create.mutate();
  };

  return (
    <div>
      <h1>Usuários</h1>
      <p>
        Contas incompletas: gere o link de convite e encaminhe ao jogador (sem e-mail automático).
        Admin pode criar staff/admin.
      </p>
      {error && <p className="error">{error}</p>}
      {inviteMsg && <p className="success">{inviteMsg}</p>}

      <form onSubmit={onCreate} className="card" style={{ marginBottom: "1.5rem" }}>
        <h2>Criar conta (rápida / incomplete)</h2>
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
        <button className="primary" type="submit" disabled={create.isPending}>
          Criar
        </button>
      </form>

      <div className="form-row">
        <label>Buscar</label>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="nome, e-mail ou celular" />
      </div>
      {isLoading && <p>Carregando...</p>}
      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>E-mail</th>
            <th>Celular</th>
            <th>Papel</th>
            <th>Status</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {data.map((u) => (
            <tr key={u.id}>
              <td>{u.display_name}</td>
              <td>{u.email}</td>
              <td>{u.phone}</td>
              <td>{u.role}</td>
              <td>{u.status}</td>
              <td>
                {u.status === "incomplete" && (
                  <button className="secondary" type="button" onClick={() => invite.mutate(u.id)}>
                    {invite.isPending ? "Gerando…" : "Gerar e copiar convite"}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
