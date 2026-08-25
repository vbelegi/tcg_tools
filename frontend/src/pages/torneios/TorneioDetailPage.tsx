import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type ClipboardEvent, type KeyboardEvent } from "react";
import { Link, useParams } from "react-router-dom";

import { ConfirmModal } from "../../components/ConfirmModal";
import { PlayerPickerModal } from "../../components/PlayerPickerModal";
import { RoundMatchesTable } from "../../components/RoundMatchesTable";
import { SeFormatOptions, type SeBoConfig } from "../../components/SeFormatOptions";
import { api } from "../../api/client";
import { parsePastedNames } from "../../utils/pasteNames";
import { playersMissingSeed, seedRequirementMessage } from "../../utils/seeds";

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
  const [thirdPlaceMatch, setThirdPlaceMatch] = useState(false);
  const [seBoConfig, setSeBoConfig] = useState<SeBoConfig>({});
  const [seOptionsDirty, setSeOptionsDirty] = useState(false);
  const [playerAddedFlash, setPlayerAddedFlash] = useState(false);
  const playerNameRef = useRef<HTMLInputElement>(null);
  const playerSeedRef = useRef<HTMLInputElement>(null);
  const nextRoundBtnRef = useRef<HTMLButtonElement>(null);
  const finalizeBtnRef = useRef<HTMLButtonElement>(null);

  const { data: torneio } = useQuery({
    queryKey: ["torneio", eventId],
    queryFn: () => api.getTorneio(eventId),
  });

  const completedRoundNum = torneio?.completed_rounds ?? 0;
  const { data: lastCompletedRound } = useQuery({
    queryKey: ["rodada", eventId, completedRoundNum],
    queryFn: () => api.getRodada(eventId, completedRoundNum),
    enabled: Boolean(torneio?.between_rounds && completedRoundNum > 0),
  });

  useEffect(() => {
    if (torneio?.status === "draft") {
      playerNameRef.current?.focus();
    }
  }, [torneio?.status, eventId]);

  useEffect(() => {
    if (!playerAddedFlash) return;
    const t = window.setTimeout(() => setPlayerAddedFlash(false), 2000);
    return () => window.clearTimeout(t);
  }, [playerAddedFlash]);

  const focusNameField = () => {
    requestAnimationFrame(() => playerNameRef.current?.focus());
  };

  const addPlayer = useMutation({
    mutationFn: async (payload: { names: string[]; seed?: number }) => {
      for (const name of payload.names) {
        await api.addJogador(eventId, name, payload.seed);
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      setPlayerName("");
      setPlayerSeed("");
      setError("");
      setPlayerAddedFlash(true);
      focusNameField();
    },
    onError: (e) => {
      setError((e as Error).message);
      focusNameField();
    },
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

  const saveSeOptions = useMutation({
    mutationFn: () =>
      api.updateTorneio(eventId, {
        third_place_match: thirdPlaceMatch,
        se_bo_config: Object.keys(seBoConfig).length > 0 ? seBoConfig : null,
      }),
    onSuccess: () => {
      setSeOptionsDirty(false);
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
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

  useEffect(() => {
    if (!torneio || torneio.status !== "draft" || torneio.format !== "single_elimination") return;
    if (!seOptionsDirty) {
      setThirdPlaceMatch(torneio.third_place_match ?? false);
      setSeBoConfig(torneio.se_bo_config ?? {});
    }
  }, [torneio, seOptionsDirty]);

  useEffect(() => {
    if (!torneio?.between_rounds) return;
    requestAnimationFrame(() => {
      if (torneio.can_start_next_round) nextRoundBtnRef.current?.focus();
      else if (torneio.can_finalize) finalizeBtnRef.current?.focus();
    });
  }, [torneio?.between_rounds, torneio?.can_start_next_round, torneio?.can_finalize, torneio?.completed_rounds]);

  if (!torneio) return <p>Carregando...</p>;

  const isDraft = torneio.status === "draft";
  const isRunning = torneio.status === "running";
  const isFinished = torneio.status === "finished";
  const hasActiveRound = isRunning && !torneio.between_rounds && torneio.current_round > 0;
  const activePlayers =
    torneio.players?.filter((p) => !p.dropped_at).map((p) => ({ id: p.id, name: p.name })) ?? [];

  const draftPlayers = torneio.players ?? [];
  const missingSeedPlayers = playersMissingSeed(draftPlayers);
  const missingSeedIds = new Set(missingSeedPlayers.map((p) => p.id));
  const seedsIncomplete = missingSeedPlayers.length > 0;
  const seedRequired = draftPlayers.some((p) => p.seed != null);
  const seedErrorMessage = seedRequirementMessage(missingSeedPlayers.map((p) => p.name));
  const canSubmitPlayer =
    Boolean(playerName.trim()) &&
    !addPlayer.isPending &&
    !(seedRequired && !playerSeed.trim());

  const submitPlayer = () => {
    if (!canSubmitPlayer) return;
    addPlayer.mutate({
      names: [playerName.trim()],
      seed: playerSeed.trim() ? parseInt(playerSeed, 10) : undefined,
    });
  };

  const clearPlayerForm = () => {
    setPlayerName("");
    setPlayerSeed("");
    setError("");
    focusNameField();
  };

  const handleNameKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      clearPlayerForm();
      return;
    }
    if (e.key !== "Enter") return;
    e.preventDefault();
    if (!playerName.trim() || addPlayer.isPending) return;
    if (seedRequired) {
      playerSeedRef.current?.focus();
      return;
    }
    submitPlayer();
  };

  const handleSeedKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      clearPlayerForm();
      return;
    }
    if (e.key !== "Enter") return;
    e.preventDefault();
    submitPlayer();
  };

  const handleNamePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    const names = parsePastedNames(e.clipboardData.getData("text"));
    if (names.length <= 1) return;
    e.preventDefault();
    if (seedRequired) {
      setError(
        "Com seeding ativo, cole um nome por vez e informe o seed — ou remova os seeds existentes.",
      );
      return;
    }
    addPlayer.mutate({ names });
  };

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
      {torneio.config_warnings?.map((w) => (
        <p key={w} className="warning" role="status">
          {w}
        </p>
      ))}

      {isDraft && (
        <>
          <h2>Jogadores ({torneio.players?.length ?? 0})</h2>
          {torneio.format === "single_elimination" && (
            <>
              <SeFormatOptions
                thirdPlaceMatch={thirdPlaceMatch}
                onThirdPlaceMatchChange={(v) => {
                  setThirdPlaceMatch(v);
                  setSeOptionsDirty(true);
                }}
                seBoConfig={seBoConfig}
                onSeBoConfigChange={(v) => {
                  setSeBoConfig(v);
                  setSeOptionsDirty(true);
                }}
                defaultBestOf={torneio.best_of}
                maxRounds={
                  torneio.recommended_rounds ??
                  Math.ceil(Math.log2(Math.max(torneio.players?.length ?? 8, 2)))
                }
              />
              {seOptionsDirty && (
                <p className="warning" style={{ marginBottom: "0.5rem" }}>
                  Opções SE alteradas — salve antes de iniciar. Bo global atual: {torneio.best_of}.
                </p>
              )}
              {seOptionsDirty && (
                <button
                  className="secondary"
                  style={{ marginBottom: "1rem" }}
                  onClick={() => saveSeOptions.mutate()}
                  disabled={saveSeOptions.isPending}
                >
                  Salvar opções SE
                </button>
              )}
            </>
          )}
          {torneio.max_rounds != null && torneio.players && torneio.players.length >= 4 && (
            <p className="warning">
              Recomendado: {torneio.recommended_rounds ?? "—"} rodadas para {torneio.players.length}{" "}
              jogadores
              {torneio.max_rounds < (torneio.recommended_rounds ?? 0) &&
                ` (configurado: ${torneio.max_rounds})`}
            </p>
          )}
          {seedsIncomplete && (
            <p className="error" role="alert">
              {seedErrorMessage} Remova e cadastre de novo com seed, ou remova os seeds
              existentes.
            </p>
          )}
          <ul className="player-draft-list">
            {torneio.players?.map((p) => {
              const needsSeed = missingSeedIds.has(p.id);
              return (
                <li
                  key={p.id}
                  className={needsSeed ? "player-row player-row-seed-missing" : "player-row"}
                >
                  <span>
                    {p.name}
                    {p.seed != null ? ` (seed ${p.seed})` : needsSeed ? " — falta seed" : ""}
                  </span>{" "}
                  <button
                    className="secondary"
                    onClick={() => setRemoveTarget({ id: p.id, name: p.name })}
                  >
                    Remover
                  </button>
                </li>
              );
            })}
          </ul>
          <div className="form-row">
            <label htmlFor="player-name">Nome</label>
            <input
              id="player-name"
              ref={playerNameRef}
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              onKeyDown={handleNameKeyDown}
              onPaste={handleNamePaste}
              placeholder={
                seedRequired
                  ? "Nome · Enter vai para o seed"
                  : "Nome · Enter adiciona · cole lista"
              }
              aria-describedby="player-name-hint"
              disabled={addPlayer.isPending}
            />
            <p id="player-name-hint" className="field-hint">
              Enter adiciona
              {seedRequired ? " (após o seed)" : ""}. Esc limpa. Cole vários nomes (linhas/vírgulas)
              sem seeding.
            </p>
          </div>
          <div className="form-row">
            <label htmlFor="player-seed">
              Seed {seedRequired ? "(obrigatório — seeding já iniciado)" : "(opcional)"}
            </label>
            <input
              id="player-seed"
              ref={playerSeedRef}
              type="number"
              value={playerSeed}
              onChange={(e) => setPlayerSeed(e.target.value)}
              onKeyDown={handleSeedKeyDown}
              className={seedRequired && !playerSeed.trim() ? "input-invalid" : undefined}
              aria-invalid={seedRequired && !playerSeed.trim()}
              aria-describedby={seedRequired ? "player-seed-hint" : undefined}
              disabled={addPlayer.isPending}
            />
            {seedRequired && !playerSeed.trim() && (
              <p id="player-seed-hint" className="error-text" style={{ fontSize: "0.85rem", margin: "0.25rem 0 0" }}>
                Informe um seed para este jogador, ou remova os seeds dos demais.
              </p>
            )}
          </div>
          <button
            className="secondary"
            type="button"
            onClick={submitPlayer}
            disabled={!canSubmitPlayer}
          >
            {addPlayer.isPending ? "Adicionando…" : "Adicionar jogador"}
          </button>
          {playerAddedFlash && (
            <div className="save-feedback success" role="status" aria-live="polite">
              Jogador(es) adicionado(s)
            </div>
          )}
          <div style={{ marginTop: "1.5rem" }}>
            <button
              className="primary"
              onClick={handleIniciar}
              disabled={
                (torneio.players?.length ?? 0) < 4 ||
                seedsIncomplete ||
                iniciar.isPending
              }
              title={
                seedsIncomplete
                  ? "Corrija o seeding parcial antes de iniciar"
                  : undefined
              }
            >
              Iniciar torneio
            </button>
            {seedsIncomplete && (
              <p className="error-text" style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>
                Não é possível iniciar com apenas alguns jogadores com seed.
              </p>
            )}
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
          {lastCompletedRound && (
            <>
              <p style={{ fontSize: "0.9rem", opacity: 0.85, marginTop: "1rem" }}>
                Confira os resultados da rodada {lastCompletedRound.number} antes de iniciar a
                próxima. Se algo estiver errado, use <strong>Reabrir rodada</strong>.
              </p>
              <RoundMatchesTable
                title={`Resumo — rodada ${lastCompletedRound.number}`}
                matches={lastCompletedRound.matches}
              />
            </>
          )}
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
                ref={nextRoundBtnRef}
                className="primary"
                onClick={() => iniciarProxima.mutate()}
                disabled={iniciarProxima.isPending}
              >
                Iniciar rodada {(torneio.completed_rounds ?? 0) + 1}
              </button>
            )}
            {torneio.can_finalize && (
              <button
                ref={finalizeBtnRef}
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
