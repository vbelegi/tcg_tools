import { useEffect, useRef } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { PromoEnrollReason, PromoEnrollResult } from "../../api/types";

const OK_REASONS = new Set<PromoEnrollReason>(["ok", "needs_verification"]);
const WARN_REASONS = new Set<PromoEnrollReason>(["needs_auth", "already_enrolled"]);

function tone(reason: PromoEnrollReason): "ok" | "warn" | "error" {
  if (OK_REASONS.has(reason)) return "ok";
  if (WARN_REASONS.has(reason)) return "warn";
  return "error";
}

export function AcaoParticipacaoPage() {
  const { token = "" } = useParams();
  const [, setParams] = useSearchParams();
  const completeStarted = useRef(false);

  const { data: me, isFetched: meFetched } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });

  const enroll = useQuery({
    queryKey: ["promo-enroll", token],
    queryFn: () => api.enrollPromo(token),
    enabled: Boolean(token) && meFetched,
    staleTime: Infinity,
    gcTime: Infinity,
    retry: false,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const complete = useMutation({
    mutationFn: () => api.completePromoEnroll(),
  });

  useEffect(() => {
    if (enroll.data?.reason !== "needs_auth") return;
    if (me) {
      if (!completeStarted.current) {
        completeStarted.current = true;
        complete.mutate();
      }
      return;
    }
    setParams(
      (prev) => {
        if (prev.get("auth")) return prev;
        const next = new URLSearchParams(prev);
        next.set("auth", "login");
        next.set("next", `/acoes/participar/${token}`);
        return next;
      },
      { replace: true },
    );
    // complete.mutate is stable enough; avoid retriggering on mutation identity
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enroll.data?.reason, me, token, setParams]);

  if (enroll.isLoading || !meFetched) return <p>Carregando...</p>;
  if (enroll.isError && !enroll.data) {
    return (
      <div className="promo-enroll">
        <h1>Inscrição</h1>
        <p className="error">{(enroll.error as Error).message}</p>
        <p>
          <Link to="/acoes">Ver ações promocionais</Link>
        </p>
      </div>
    );
  }

  if (complete.isPending) return <p>Concluindo inscrição…</p>;
  if (complete.isError && !complete.data) {
    return (
      <div className="promo-enroll">
        <h1>Inscrição</h1>
        <p className="error">{(complete.error as Error).message}</p>
        <p>
          <Link to="/acoes">Ver ações promocionais</Link>
        </p>
      </div>
    );
  }

  const result: PromoEnrollResult | undefined = complete.data ?? enroll.data;
  if (!result) return <p>Carregando...</p>;

  const boxTone = tone(result.reason);

  return (
    <div className="promo-enroll">
      <h1>{result.action_name || "Inscrição"}</h1>
      <div className={`promo-enroll-box promo-enroll-box--${boxTone}`} role="status">
        <p>{result.message}</p>
        {result.reason === "needs_verification" && (
          <p>
            <Link to="/conta/verificar-email">Confirmar e-mail</Link>
          </p>
        )}
      </div>
      {result.action_id != null && (
        <p>
          <Link to={`/acoes/${result.action_id}`}>Ver ação promocional</Link>
        </p>
      )}
      <p>
        <Link to="/acoes" className="torneio-back">
          ← Ações Promocionais
        </Link>
      </p>
    </div>
  );
}
