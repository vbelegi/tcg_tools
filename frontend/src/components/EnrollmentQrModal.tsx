import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { PromoEnrollmentToken } from "../api/types";
import { formatCountdown } from "../pages/acoes/promoFormat";
import { enrollHref, qrSvg } from "../utils/qrSvg";
import { Modal } from "./Modal";

type Props = {
  open: boolean;
  actionId: number;
  onClose: () => void;
};

export function EnrollmentQrModal({ open, actionId, onClose }: Props) {
  const [token, setToken] = useState<PromoEnrollmentToken | null>(null);
  const [svg, setSvg] = useState("");
  const [issuedAt, setIssuedAt] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [generation, setGeneration] = useState(0);

  useEffect(() => {
    if (!open) {
      setToken(null);
      setSvg("");
      setIssuedAt(null);
      setError("");
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    setToken(null);
    setSvg("");
    setIssuedAt(null);
    void api
      .createPromoEnrollmentToken(actionId)
      .then(async (issued) => {
        if (cancelled) return;
        const markup = await qrSvg(enrollHref(issued));
        if (cancelled) return;
        setToken(issued);
        setSvg(markup);
        const stamp = Date.now();
        setIssuedAt(stamp);
        setNow(stamp);
      })
      .catch((e) => {
        if (!cancelled) setError((e as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, actionId, generation]);

  useEffect(() => {
    if (!open || issuedAt == null) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [open, issuedAt]);

  const remaining =
    token && issuedAt != null
      ? Math.max(0, token.expires_in_seconds - Math.floor((now - issuedAt) / 1000))
      : 0;
  const expired = Boolean(token) && remaining <= 0;

  return (
    <Modal
      open={open}
      title="Inscrever novo participante"
      onClose={onClose}
      footer={
        <>
          <button
            className="secondary"
            type="button"
            onClick={() => setGeneration((n) => n + 1)}
            disabled={loading}
          >
            {loading ? "Gerando…" : "Gerar novo QR"}
          </button>
          <button className="primary" type="button" onClick={onClose}>
            Fechar
          </button>
        </>
      }
    >
      {error && <p className="error">{error}</p>}
      {loading && <p>Gerando QR…</p>}
      {token && (
        <>
          <p className="promo-qr-timer" role="timer">
            {expired ? "Link expirado. Gere outro QR." : `Validade: ${formatCountdown(remaining)}`}
          </p>
          <div className={expired ? "promo-qr promo-qr--expired" : "promo-qr"}>
            {svg ? (
              <div className="promo-qr-svg" dangerouslySetInnerHTML={{ __html: svg }} />
            ) : (
              <p>Carregando QR…</p>
            )}
          </div>
          <p className="field-hint">
            Peça para a pessoa apontar a câmera do celular para o código. O link vale uma vez e
            por 10 minutos.
          </p>
        </>
      )}
    </Modal>
  );
}
