import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { ListFilterBar } from "../components/ListFilterBar";

function parseOptionalId(raw: string): number | undefined {
  const t = raw.trim();
  if (!t) return undefined;
  const n = Number(t);
  return Number.isInteger(n) && n > 0 ? n : undefined;
}

export function AuditLogsPage() {
  const [action, setAction] = useState("");
  const [actorId, setActorId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const actorUserId = parseOptionalId(actorId);
  const targetUserId = parseOptionalId(targetId);

  const { data, isLoading, error } = useQuery({
    queryKey: ["audit-logs", action, actorUserId, targetUserId, from, to, offset],
    queryFn: () =>
      api.listAuditLogs({
        action: action.trim() || undefined,
        actor_user_id: actorUserId,
        target_user_id: targetUserId,
        from: from || undefined,
        to: to || undefined,
        limit,
        offset,
      }),
  });

  const total = data?.total ?? 0;
  const items = data?.items ?? [];
  const canPrev = offset > 0;
  const canNext = offset + limit < total;
  const idFilterError =
    (actorId.trim() !== "" && actorUserId == null) ||
    (targetId.trim() !== "" && targetUserId == null);

  return (
    <div className="admin-page">
      <header className="torneio-manage-header">
        <div>
          <h1>Logs da plataforma</h1>
          <p className="torneio-manage-meta">Auditoria de ações sensíveis · {total} registro(s)</p>
        </div>
      </header>

      {error ? <p className="error">{(error as Error).message}</p> : null}
      {idFilterError ? <p className="error">IDs de ator/alvo devem ser números inteiros positivos.</p> : null}

      <ListFilterBar
        searchValue={action}
        onSearchChange={(v) => {
          setAction(v);
          setOffset(0);
        }}
        searchLabel="Ação"
        searchPlaceholder="ex.: user.role_change"
        searchId="audit-action"
        dateFrom={from}
        dateTo={to}
        onDateFromChange={(v) => {
          setFrom(v);
          setOffset(0);
        }}
        onDateToChange={(v) => {
          setTo(v);
          setOffset(0);
        }}
        resultCount={total}
      />

      <div className="admin-form-grid" style={{ marginTop: "0.75rem" }}>
        <div className="form-row">
          <label htmlFor="audit-actor-id">ID do ator</label>
          <input
            id="audit-actor-id"
            type="text"
            inputMode="numeric"
            value={actorId}
            placeholder="opcional"
            onChange={(e) => {
              setActorId(e.target.value);
              setOffset(0);
            }}
          />
        </div>
        <div className="form-row">
          <label htmlFor="audit-target-id">ID do alvo</label>
          <input
            id="audit-target-id"
            type="text"
            inputMode="numeric"
            value={targetId}
            placeholder="opcional"
            onChange={(e) => {
              setTargetId(e.target.value);
              setOffset(0);
            }}
          />
        </div>
      </div>
      <p className="field-hint">Os IDs aparecem na tabela (ator/alvo). Deixe em branco para não filtrar.</p>

      {isLoading && <p>Carregando...</p>}

      <section className="resultado-section">
        <div className="resultado-table-wrap">
          <table className="resultado-table">
            <thead>
              <tr>
                <th>Quando</th>
                <th>Ação</th>
                <th>Ator</th>
                <th>Alvo</th>
                <th>IP</th>
                <th>Meta</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id}>
                  <td>{row.created_at ? new Date(row.created_at).toLocaleString("pt-BR") : "—"}</td>
                  <td>
                    <code>{row.action}</code>
                  </td>
                  <td>
                    {row.actor_display_name ?? (row.actor_user_id != null ? `#${row.actor_user_id}` : "—")}
                    {row.actor_user_id != null ? (
                      <span className="field-hint"> #{row.actor_user_id}</span>
                    ) : null}
                  </td>
                  <td>
                    {row.target_display_name ??
                      (row.target_user_id != null ? `#${row.target_user_id}` : "—")}
                    {row.target_user_id != null ? (
                      <span className="field-hint"> #{row.target_user_id}</span>
                    ) : null}
                  </td>
                  <td>{row.ip ?? "—"}</td>
                  <td>
                    <code style={{ fontSize: "0.85em" }}>
                      {row.meta ? JSON.stringify(row.meta) : "—"}
                    </code>
                  </td>
                </tr>
              ))}
              {!isLoading && items.length === 0 && (
                <tr>
                  <td colSpan={6}>Nenhum registro.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="profile-privacy-actions" style={{ marginTop: "1rem" }}>
          <button
            type="button"
            className="secondary"
            disabled={!canPrev}
            onClick={() => setOffset((o) => Math.max(0, o - limit))}
          >
            Anterior
          </button>
          <button
            type="button"
            className="secondary"
            disabled={!canNext}
            onClick={() => setOffset((o) => o + limit)}
          >
            Próxima
          </button>
        </div>
      </section>
    </div>
  );
}
