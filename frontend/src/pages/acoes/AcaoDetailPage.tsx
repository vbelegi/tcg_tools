import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { api } from "../../api/client";
import { RegulationUploadField } from "../../components/RegulationUploadField";
import type { PromoAction } from "../../api/types";
import { formatPeriod, phaseLabel, promoPhase } from "./promoFormat";

export function AcaoDetailPage() {
  const { id } = useParams();
  const actionId = Number(id);
  const qc = useQueryClient();
  const [, setParams] = useSearchParams();

  const { data: me, isFetched: meFetched } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const canManage = me && (me.role === "admin" || me.role === "staff");

  const {
    data: action,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["acao", actionId, me?.id ?? "guest"],
    queryFn: () => api.getPromoAction(actionId),
    enabled: meFetched && Number.isFinite(actionId),
    retry: false,
  });

  const publish = useMutation({
    mutationFn: () => api.publishPromoAction(actionId),
    onSuccess: (updated) => applyUpdate(updated),
  });

  const applyUpdate = (updated: PromoAction) => {
    qc.setQueryData(["acao", actionId, me?.id ?? "guest"], updated);
    void qc.invalidateQueries({ queryKey: ["acoes"] });
  };

  const openAuth = (mode: "login" | "register") => {
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("auth", mode);
        return next;
      },
      { replace: true },
    );
  };

  if (isLoading) return <p>Carregando...</p>;
  if (isError || !action) {
    return (
      <div>
        <h1>Ação não encontrada</h1>
        <p className="muted">
          Esta ação promocional não existe ou não está disponível.{" "}
          <Link to="/acoes">Ver todas as ações</Link>
        </p>
      </div>
    );
  }

  const phase = promoPhase(action);

  return (
    <div className="promo-detail">
      <Link to="/acoes" className="torneio-back">
        ← Ações Promocionais
      </Link>
      <div className="page-header">
        <div>
          <h1>{action.name}</h1>
          <p className="page-header-meta">
            {formatPeriod(action.start_date, action.end_date)} · {action.type_label}
          </p>
          <p className="promo-card-badges">
            <span className="badge">{phaseLabel(phase)}</span>
            {!action.published && <span className="badge badge-warn">rascunho</span>}
            {canManage && action.participant_count != null && (
              <span className="badge">{action.participant_count} inscritos</span>
            )}
          </p>
        </div>
        {canManage && !action.published && (
          <button
            className="primary"
            type="button"
            onClick={() => publish.mutate()}
            disabled={publish.isPending}
          >
            {publish.isPending ? "Publicando…" : "Publicar"}
          </button>
        )}
      </div>

      {publish.isError && <p className="error">{(publish.error as Error).message}</p>}

      {action.description && <p className="promo-detail-desc">{action.description}</p>}

      {action.regulation ? (
        <p>
          <a href={action.regulation.url} target="_blank" rel="noreferrer">
            Regulamento ({action.regulation.display_name})
          </a>
        </p>
      ) : (
        <p className="muted">Regulamento ainda não disponível.</p>
      )}

      <section className="promo-participation">
        <h2>Como participar</h2>
        {action.my_participation && (
          <div className="promo-enrolled-notice" role="status">
            {action.my_participation.status === "confirmed" ? (
              <p>Você já está participando desta Ação Promocional.</p>
            ) : (
              <p>
                Inscrição pendente; confirme seu e-mail.{" "}
                <Link to="/conta/verificar-email">Reenviar link de verificação</Link>
              </p>
            )}
          </div>
        )}
        {action.how_to_participate && <p>{action.how_to_participate}</p>}

        {meFetched && !me && (
          <div className="promo-guest-notice">
            <p>
              Para participar das ações promocionais é necessário ter uma conta e estar logado
              na plataforma.
            </p>
            <div className="promo-guest-actions">
              <button className="primary" type="button" onClick={() => openAuth("login")}>
                Entrar
              </button>
              <button className="secondary" type="button" onClick={() => openAuth("register")}>
                Criar conta
              </button>
            </div>
          </div>
        )}
      </section>

      {canManage && (
        <section className="promo-manage">
          <h2>Gerenciamento</h2>
          <RegulationUploadField
            actionId={action.id}
            current={action.regulation}
            history={action.regulation_versions}
            onUploaded={applyUpdate}
          />
        </section>
      )}
    </div>
  );
}
