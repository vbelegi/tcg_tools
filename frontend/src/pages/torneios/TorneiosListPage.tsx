import { useQuery } from "@tanstack/react-query";
import { useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../../api/client";
import { isAdminRole, isStaffRole } from "../../utils/roles";
import { ListFilterBar } from "../../components/ListFilterBar";

export function TorneiosListPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const onlyActive = params.get("active") === "1";
  const dateFrom = params.get("from") ?? "";
  const dateTo = params.get("to") ?? "";

  const { data: me, isFetched: meFetched } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const canManage = me && isStaffRole(me.role);
  const isGuest = meFetched && !me;

  const { data, isLoading } = useQuery({
    queryKey: ["torneios", me?.id ?? "guest", q, onlyActive, dateFrom, dateTo],
    queryFn: () =>
      api.listTorneios({
        q: q || undefined,
        active: onlyActive || undefined,
        from: dateFrom || undefined,
        to: dateTo || undefined,
      }),
    enabled: meFetched,
  });

  const update = useCallback(
    (changes: { q?: string; active?: boolean; from?: string; to?: string }) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (changes.q !== undefined) {
            if (changes.q) next.set("q", changes.q);
            else next.delete("q");
          }
          if (changes.active !== undefined) {
            if (changes.active) next.set("active", "1");
            else next.delete("active");
          }
          if (changes.from !== undefined) {
            if (changes.from) next.set("from", changes.from);
            else next.delete("from");
          }
          if (changes.to !== undefined) {
            if (changes.to) next.set("to", changes.to);
            else next.delete("to");
          }
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  const onSearchChange = useCallback((value: string) => update({ q: value }), [update]);
  const hasFilters = Boolean(q) || onlyActive || Boolean(dateFrom) || Boolean(dateTo);

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <h1>Torneios</h1>
        {canManage && (
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {isAdminRole(me.role) && (
              <Link to="/torneios/externo" className="secondary">
                Importar externo
              </Link>
            )}
            <Link to="/torneios/novo" className="primary">
              Novo torneio
            </Link>
          </div>
        )}
      </div>

      <ListFilterBar
        searchId="torneios-filter-q"
        searchLabel="Buscar por nome"
        searchPlaceholder="Ex.: liga semanal"
        searchValue={q}
        onSearchChange={onSearchChange}
        dateFrom={dateFrom}
        dateTo={dateTo}
        onDateFromChange={(value) => update({ from: value })}
        onDateToChange={(value) => update({ to: value })}
        toggles={[
          {
            id: "active",
            label: "Somente não encerrados",
            checked: onlyActive,
            onChange: (checked) => update({ active: checked }),
          },
        ]}
        resultCount={data?.length}
      />

      {isLoading && <p>Carregando...</p>}
      {data && data.length === 0 && (
        <p className="muted">
          {hasFilters
            ? "Nenhum torneio encontrado com esses filtros."
            : isGuest
              ? "Nenhum torneio aberto ou finalizado no momento."
              : "Nenhum torneio cadastrado."}
        </p>
      )}
      <div className="card-grid" style={{ marginTop: "1rem" }}>
        {data?.map((t) => {
          const to =
            t.status === "finished" ? `/torneios/${t.id}/resultado` : `/torneios/${t.id}`;
          return (
            <Link key={t.id} to={to} className="card">
              <h2>{t.name}</h2>
              <p>
                {t.event_date} — <span className="badge">{t.status}</span>
                {t.source === "external" && <span className="badge"> externo</span>}
                {t.status === "draft" && t.registration_open && (
                  <span className="badge"> inscrição aberta</span>
                )}
                {t.pairing_mode === "manual" && <span className="badge"> sem rodadas</span>}
              </p>
              <p>
                {t.format === "swiss" ? "Suíço" : "Eliminatória"} · {t.player_count} jogadores
                {t.entry_fee != null && ` · R$ ${t.entry_fee}`}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
