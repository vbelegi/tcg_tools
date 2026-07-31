import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ConfirmModal } from "../../components/ConfirmModal";
import { PlayerPickerModal } from "../../components/PlayerPickerModal";
import { api } from "../../api/client";

export function TorneioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const eventId = Number(id);
  const qc = useQueryClient();
  const [playerName, setPlayerName] = useState("");
  const [playerSeed, setPlayerSeed] = useState("");
  const [error, setError] = useState("");
  const [removeTarget, setRemoveTarget] = useState<{ id: number; name: string } | null>(null);
  const [dropModalOpen, setDropModalOpen] = useState(false);
  const [finalizarModalOpen, setFinalizarModalOpen] = useState(false);
  const [reabrirModalOpen, setReabrirModalOpen] = useState(false);

  const { data: torneio } = useQuery({
    queryKey: ["torneio", eventId],
    queryFn: () => api.getTorneio(eventId),
  });

  const addPlayer = useMutation({
    mutationFn: () =>
      api.addJogador(eventId, playerName, playerSeed ? parseInt(playerSeed, 10) : undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      setPlayerName("");
      setPlayerSeed("");
      setError("");
    },
    onError: (e) => setError((e as Error).message),
  });

  const removePlayer = useMutation({
    mutationFn: (pid: number) => api.removeJogador(eventId, pid),
    onSuccess: () => {
      setRemoveTarget(null);
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const iniciar = useMutation({
    mutationFn: () => api.iniciarTorneio(eventId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["torneio", eventId] }),
    onError: (e) => setError((e as Error).message),
  });

  const iniciarProxima = useMutation({
    mutationFn: () => api.iniciarProximaRodada(eventId),
    onSuccess: (t) => {
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      window.location.href = `/torneios/${eventId}/rodadas/${t.current_round}`;
    },
    onError: (e) => setError((e as Error).message),
  });

  const reabrirRodada = useMutation({
    mutationFn: () => api.reabrirRodada(eventId),
    onSuccess: (t) => {
      setReabrirModalOpen(false);
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      window.location.href = `/torneios/${eventId}/rodadas/${t.current_round}`;
    },
    onError: (e) => setError((e as Error).message),
  });

  const dropPlayer = useMutation({
    mutationFn: (pid: number) => api.dropJogador(eventId, pid, false),
    onSuccess: () => {
      setDropModalOpen(false);
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const finalizar = useMutation({
    mutationFn: () => api.finalizar(eventId),
    onSuccess: () => {
      setFinalizarModalOpen(false);
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      window.location.href = `/torneios/${eventId}/resultado`;
    },
    onError: (e) => setError((e as Error).message),
  });

  const handleIniciar = () => {
    if (!torneio) return;
    const n = torneio.players?.length ?? 0;
    const rec = torneio.recommended_rounds ?? Math.ceil(Math.log2(Math.max(n, 4)));
    if (torneio.max_rounds != null && torneio.max_rounds < rec) {
      const ok = window.confirm(
        `Rodadas máximas (${torneio.max_rounds}) é menor que o recomendado (${rec}) para ${n} jogadores. Deseja iniciar mesmo assim?`,
      );
      if (!ok) return;
    }
    iniciar.mutate();
  };

  if (!torneio) return <p>Carregando...</p>;

  const isDraft = torneio.status === "draft";
  const isRunning = torneio.status === "running";
  const isFinished = torneio.status === "finished";
  const hasActiveRound = isRunning && !torneio.between_rounds && torneio.current_round > 0;
  const activePlayers =
    torneio.players?.filter((p) => !p.dropped_at).map((p) => ({ id: p.id, name: p.name })) ?? [];

  const reabrirMessage = hasActiveRound
    ? `Reabrir rodada ${torneio.current_round - 1}? A rodada ${torneio.current_round} será removida e o pairing refeito ao avançar.`
    : `Reabrir rodada ${torneio.completed_rounds} para corrigir resultados?`;

  return (
    <div>
      <h1>{torneio.name}</h1>
      <p>
        {torneio.event_date} · {torneio.format === "swiss" ? "Suíço" : "Eliminatória"} ·{" "}
        <span className="badge">{torneio.status}</span>
      </p>

      <div className="stepper">
        <span className={isDraft ? "active" : ""}>Jogadores</span>
        <span className={isRunning ? "active" : ""}>Rodadas</span>
        <span className={isFinished ? "active" : ""}>Resultado</span>
      </div>

      {error && <p className="error">{error}</p>}

      {isDraft && (
        <>
          <h2>Jogadores ({torneio.players?.length ?? 0})</h2>
          {torneio.max_rounds != null && torneio.players && torneio.players.length >= 4 && (
            <p className="warning">
              Recomendado: {torneio.recommended_rounds ?? "—"} rodadas para {torneio.players.length}{" "}
              jogadores
              {torneio.max_rounds < (torneio.recommended_rounds ?? 0) &&
                ` (configurado: ${torneio.max_rounds})`}
            </p>
          )}
          <ul>
            {torneio.players?.map((p) => (
              <li key={p.id} style={{ marginBottom: "0.35rem" }}>
                {p.name}
                {p.seed != null && ` (seed ${p.seed})`}{" "}
                <button
                  className="secondary"
                  onClick={() => setRemoveTarget({ id: p.id, name: p.name })}
                >
                  Remover
                </button>
              </li>
            ))}
          </ul>
          <div className="form-row">
            <label>Nome</label>
            <input value={playerName} onChange={(e) => setPlayerName(e.target.value)} />
          </div>
          <div className="form-row">
            <label>Seed (opcional)</label>
            <input type="number" value={playerSeed} onChange={(e) => setPlayerSeed(e.target.value)} />
          </div>
          <button
            className="secondary"
            onClick={() => addPlayer.mutate()}
            disabled={!playerName.trim() || addPlayer.isPending}
          >
            Adicionar jogador
          </button>
          <div style={{ marginTop: "1.5rem" }}>
            <button
              className="primary"
              onClick={handleIniciar}
              disabled={(torneio.players?.length ?? 0) < 4 || iniciar.isPending}
            >
              Iniciar torneio
            </button>
          </div>
        </>
      )}

      {isRunning && hasActiveRound && (
        <>
          <p>
            Rodada ativa: {torneio.current_round} / {torneio.max_rounds}
          </p>
          <Link
            to={`/torneios/${eventId}/rodadas/${torneio.current_round}`}
            className="primary"
            style={{ display: "inline-block", marginTop: "1rem", padding: "0.6rem 1.25rem", borderRadius: 999 }}
          >
            Gerenciar rodada {torneio.current_round}
          </Link>
          {torneio.can_reopen_round && torneio.current_round > 1 && (
            <div style={{ marginTop: "1rem" }}>
              <button
                className="secondary"
                onClick={() => setReabrirModalOpen(true)}
                disabled={reabrirRodada.isPending}
              >
                Reabrir rodada anterior
              </button>
            </div>
          )}
        </>
      )}

      {isRunning && torneio.between_rounds && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h2>Entre rodadas</h2>
          <p>
            Rodada {torneio.completed_rounds} concluída.
            {torneio.can_start_next_round
              ? ` Próxima: rodada ${(torneio.completed_rounds ?? 0) + 1}.`
              : torneio.can_finalize
                ? " Todas as rodadas foram concluídas."
                : ""}
          </p>
          <p className="warning">Janela para drop entre rodadas (sem WO).</p>
          {activePlayers.length > 0 && (
            <div style={{ marginTop: "1rem" }}>
              <button className="secondary" onClick={() => setDropModalOpen(true)}>
                Registrar drop…
              </button>
            </div>
          )}
          <div style={{ marginTop: "1.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {torneio.can_reopen_round && (
              <button
                className="secondary"
                onClick={() => setReabrirModalOpen(true)}
                disabled={reabrirRodada.isPending}
              >
                Reabrir rodada {torneio.completed_rounds}
              </button>
            )}
            {torneio.can_start_next_round && (
              <button
                className="primary"
                onClick={() => iniciarProxima.mutate()}
                disabled={iniciarProxima.isPending}
              >
                Iniciar rodada {(torneio.completed_rounds ?? 0) + 1}
              </button>
            )}
            {torneio.can_finalize && (
              <button
                className="secondary"
                onClick={() => setFinalizarModalOpen(true)}
                disabled={finalizar.isPending}
              >
                Finalizar torneio
              </button>
            )}
          </div>
        </div>
      )}

      {isFinished && (
        <Link to={`/torneios/${eventId}/resultado`}>Ver resultado e premiação</Link>
      )}

      <ConfirmModal
        open={removeTarget != null}
        title="Remover jogador"
        message={`Remover "${removeTarget?.name}" do torneio? Esta ação não pode ser desfeita.`}
        confirmLabel="Remover"
        danger
        pending={removePlayer.isPending}
        onClose={() => setRemoveTarget(null)}
        onConfirm={() => removeTarget && removePlayer.mutate(removeTarget.id)}
      />

      <PlayerPickerModal
        open={dropModalOpen}
        title="Drop entre rodadas"
        description="O jogador sai do torneio sem walkover na partida atual. Esta ação não pode ser desfeita."
        players={activePlayers}
        confirmLabel="Confirmar drop"
        pending={dropPlayer.isPending}
        onClose={() => setDropModalOpen(false)}
        onConfirm={(pid) => dropPlayer.mutate(pid)}
      />

      <ConfirmModal
        open={finalizarModalOpen}
        title="Finalizar torneio"
        message="Finalizar calcula a premiação e encerra o evento. Confirme que todos os resultados estão corretos."
        confirmLabel="Finalizar"
        pending={finalizar.isPending}
        onClose={() => setFinalizarModalOpen(false)}
        onConfirm={() => finalizar.mutate()}
      />

      <ConfirmModal
        open={reabrirModalOpen}
        title="Reabrir rodada"
        message={reabrirMessage}
        confirmLabel="Reabrir"
        danger
        pending={reabrirRodada.isPending}
        onClose={() => setReabrirModalOpen(false)}
        onConfirm={() => reabrirRodada.mutate()}
      />
    </div>
  );
}
