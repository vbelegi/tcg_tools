import { useQuery } from "@tanstack/react-query";
import { useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../../api/client";
import { isStaffRole } from "../../utils/roles";
import { ListFilterBar } from "../../components/ListFilterBar";
import { formatPeriod, phaseLabel, promoPhase } from "./promoFormat";

export function AcoesListPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const onlyActive = params.get("active") === "1";

  const { data: me, isFetched: meFetched } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const canManage = me && isStaffRole(me.role);

  const { data, isLoading } = useQuery({
    queryKey: ["acoes", me?.id ?? "guest", q, onlyActive],
    queryFn: () => api.listPromoActions({ q: q || undefined, active: onlyActive }),
    enabled: meFetched,
  });

  const update = useCallback(
    (changes: { q?: string; active?: boolean }) => {
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
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  // Stable identity: the filter bar restarts its debounce whenever this changes.
  const onSearchChange = useCallback((value: string) => update({ q: value }), [update]);

  const hasFilters = Boolean(q) || onlyActive;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Ações Promocionais</h1>
          <p className="page-header-meta">
            Sorteios e ações da loja. Consulte o regulamento de cada ação.
          </p>
        </div>
        {canManage && (
          <Link to="/acoes/nova" className="primary">
            Criar Ação
          </Link>
        )}
      </div>

      <ListFilterBar
        searchLabel="Buscar por nome"
        searchPlaceholder="Ex.: pré-venda"
        searchValue={q}
        onSearchChange={onSearchChange}
        toggles={[
          {
            id: "active",
            label: "Somente ações ativas",
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
            ? "Nenhuma ação encontrada com esses filtros."
            : "Nenhuma ação promocional disponível no momento."}
        </p>
      )}

      <div className="card-grid" style={{ marginTop: "1rem" }}>
        {data?.map((action) => {
          const phase = promoPhase(action);
          return (
            <article key={action.id} className="card promo-card">
              <h2>
                <Link to={`/acoes/${action.id}`}>{action.name}</Link>
              </h2>
              <p className="promo-card-badges">
                <span className="badge">{phaseLabel(phase)}</span>
                {!action.published && <span className="badge badge-warn">rascunho</span>}
              </p>
              <p className="promo-card-period">{formatPeriod(action.start_date, action.end_date)}</p>
              {action.description && (
                <p className="promo-card-desc">{action.description}</p>
              )}
              {action.regulation && (
                <p>
                  <a href={action.regulation.url} target="_blank" rel="noreferrer">
                    Regulamento ({action.regulation.display_name})
                  </a>
                </p>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}
