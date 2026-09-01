import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";

import { api } from "../../api/client";

type PlacementRow = {
  player_id: number;
  name: string;
  placement: string;
  is_drop: boolean;
  decklist: string;
};

export function TorneioColocacaoPage() {
  const { id } = useParams<{ id: string }>();
  const eventId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [rows, setRows] = useState<PlacementRow[]>([]);
  const [error, setError] = useState("");

  const { data: torneio, isLoading, isError, error: loadError } = useQuery({
    queryKey: ["torneio", eventId],
    queryFn: () => api.getTorneio(eventId),
  });

  useEffect(() => {
    if (!torneio?.players) return;
    const active = torneio.players.filter(
      (p) => p.attendance !== "pending" && !p.dropped_at,
    );
    setRows(
      active.map((p, idx) => ({
        player_id: p.id,
        name: p.name,
        placement: String(idx + 1),
        is_drop: false,
        decklist: p.decklist ?? "",
      })),
    );
  }, [torneio?.id, torneio?.players]);

  const summary = useMemo(() => {
    const active = rows.filter((r) => !r.is_drop);
    const drops = rows.filter((r) => r.is_drop).length;
    return { ranked: active.length, drops };
  }, [rows]);

  const finalize = useMutation({
    mutationFn: () => {
      const placements = rows.map((r) => {
        const placement = parseInt(r.placement, 10);
        if (!r.is_drop && (!Number.isFinite(placement) || placement < 1)) {
          throw new Error(`Colocação inválida para ${r.name}.`);
        }
        return {
          player_id: r.player_id,
          placement: r.is_drop ? 999 : placement,
          is_drop: r.is_drop,
          decklist: r.decklist.trim() || null,
        };
      });
      const ranked = placements.filter((p) => !p.is_drop);
      if (ranked.length < 1) throw new Error("Informe ao menos uma colocação válida.");
      const nums = ranked.map((p) => p.placement);
      if (new Set(nums).size !== nums.length) {
        throw new Error("Colocações duplicadas entre jogadores não-drop.");
      }
      return api.finalizarColocacoes(eventId, { placements });
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      await qc.invalidateQueries({ queryKey: ["torneios"] });
      navigate(`/torneios/${eventId}/resultado`);
    },
    onError: (e) => setError((e as Error).message),
  });

  if (isLoading) return <p>Carregando...</p>;
  if (isError || !torneio) {
    return (
      <p className="error">
        {(loadError instanceof Error ? loadError.message : null) || "Torneio não encontrado."}
      </p>
    );
  }
  if (torneio.status !== "draft" || torneio.pairing_mode !== "manual") {
    return <Navigate to={`/torneios/${eventId}`} replace />;
  }

  const pending = torneio.pending_checkins ?? 0;

  return (
    <div className="admin-page">
      <header className="torneio-manage-header">
        <div>
          <Link to={`/torneios/${eventId}`} className="torneio-back">
            ← {torneio.name}
          </Link>
          <h1>Registrar colocações</h1>
          <p className="torneio-manage-meta">
            {torneio.event_date} · sem rodadas na plataforma · {rows.length} inscrito(s)
          </p>
        </div>
        <div className="torneio-manage-primary">
          <button
            type="button"
            className="primary"
            disabled={finalize.isPending || rows.length < 1 || pending > 0}
            onClick={() => {
              setError("");
              finalize.mutate();
            }}
          >
            {finalize.isPending ? "Finalizando…" : "Finalizar torneio"}
          </button>
        </div>
      </header>

      {pending > 0 && (
        <p className="warning" role="alert">
          Há {pending} inscrição(ões) pendente(s) de check-in. Resolva na ficha do torneio antes
          de finalizar.
        </p>
      )}

      <div className="externo-summary">
        <span className="entre-rodadas-chip">
          {summary.ranked} colocado{summary.ranked === 1 ? "" : "s"}
        </span>
        {summary.drops > 0 && (
          <span className="entre-rodadas-chip">{summary.drops} drop/WO</span>
        )}
      </div>

      <div className="externo-table-wrap">
        <table className="externo-table">
          <thead>
            <tr>
              <th className="externo-col-place">#</th>
              <th>Jogador</th>
              <th className="externo-col-flags">Flags</th>
              <th>Decklist</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.player_id} className={row.is_drop ? "admin-row-inactive" : undefined}>
                <td className="externo-col-place">
                  <input
                    type="number"
                    min={1}
                    value={row.is_drop ? "" : row.placement}
                    disabled={row.is_drop}
                    onChange={(e) =>
                      setRows((prev) =>
                        prev.map((r) =>
                          r.player_id === row.player_id ? { ...r, placement: e.target.value } : r,
                        ),
                      )
                    }
                    aria-label={`Colocação de ${row.name}`}
                  />
                </td>
                <td>
                  <strong>{row.name}</strong>
                </td>
                <td className="externo-col-flags">
                  <label className="externo-flag">
                    <input
                      type="checkbox"
                      checked={row.is_drop}
                      onChange={(e) =>
                        setRows((prev) =>
                          prev.map((r) =>
                            r.player_id === row.player_id
                              ? { ...r, is_drop: e.target.checked }
                              : r,
                          ),
                        )
                      }
                    />
                    Drop/WO
                  </label>
                </td>
                <td>
                  <input
                    value={row.decklist}
                    placeholder="Nome ou URL"
                    onChange={(e) =>
                      setRows((prev) =>
                        prev.map((r) =>
                          r.player_id === row.player_id ? { ...r, decklist: e.target.value } : r,
                        ),
                      )
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
