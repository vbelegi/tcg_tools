import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";

import { ConfirmModal } from "../../components/ConfirmModal";
import { Modal } from "../../components/Modal";
import { PlayerPickerModal } from "../../components/PlayerPickerModal";
import { RoundMatchesTable } from "../../components/RoundMatchesTable";
import { SeFormatOptions, type SeBoConfig } from "../../components/SeFormatOptions";
import { Switch } from "../../components/Switch";
import { TorneioDraftEditPanel } from "../../components/TorneioDraftEditPanel";
import { api } from "../../api/client";
import { isAdminRole, isStaffRole } from "../../utils/roles";
import { playersMissingSeed, seedRequirementMessage } from "../../utils/seeds";

const PHONE_HINT = "DDD + número (10 a 13 dígitos), ex.: 11987654321";

function phoneDigitCount(value: string): number {
  return (value.match(/\d/g) ?? []).length;
}

function isValidPhoneInput(value: string): boolean {
  const n = phoneDigitCount(value);
  return n >= 10 && n <= 13;
}

export function TorneioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const eventId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: me, isFetched: meFetched } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const isStaff = me && isStaffRole(me.role);
  const isAdmin = me && isAdminRole(me.role);
  const isGuest = meFetched && !me;
  const [playerName, setPlayerName] = useState("");
  const [playerSeed, setPlayerSeed] = useState("");
  const [playerEmail, setPlayerEmail] = useState("");
  const [playerPhone, setPlayerPhone] = useState("");
  const [showCreateIncomplete, setShowCreateIncomplete] = useState(false);
  const [userSearch, setUserSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [userHits, setUserHits] = useState<
    Array<{ id: number; display_name: string; email?: string; phone?: string | null }>
  >([]);
  const [searchDone, setSearchDone] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleteNameInput, setDeleteNameInput] = useState("");
  const [adminMenuOpen, setAdminMenuOpen] = useState(false);
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
  const searchRef = useRef<HTMLInputElement>(null);
  const playerSeedRef = useRef<HTMLInputElement>(null);
  const formErrorRef = useRef<HTMLParagraphElement>(null);
  const nextRoundBtnRef = useRef<HTMLButtonElement>(null);
  const finalizeBtnRef = useRef<HTMLButtonElement>(null);

  const { data: torneio, isError, error: torneioError, isLoading: torneioLoading } = useQuery({
    queryKey: ["torneio", eventId],
    queryFn: () => api.getTorneio(eventId),
  });

  const completedRoundNum = torneio?.completed_rounds ?? 0;
  const isRunningPreview = torneio?.status === "running";
  const hasActiveRoundPreview =
    isRunningPreview && !torneio?.between_rounds && (torneio?.current_round ?? 0) > 0;

  const { data: lastCompletedRound } = useQuery({
    queryKey: ["rodada", eventId, completedRoundNum],
    queryFn: () => api.getRodada(eventId, completedRoundNum),
    enabled: Boolean(torneio?.between_rounds && completedRoundNum > 0),
  });

  const { data: activeRound } = useQuery({
    queryKey: ["rodada", eventId, torneio?.current_round],
    queryFn: () => api.getRodada(eventId, torneio!.current_round),
    enabled: Boolean(hasActiveRoundPreview && (torneio?.current_round ?? 0) > 0),
  });

  const { data: liveClassificacao } = useQuery({
    queryKey: ["classificacao", eventId],
    queryFn: () => api.getClassificacao(eventId),
    enabled: Boolean(
      meFetched &&
        !isStaff &&
        torneio &&
        isRunningPreview &&
        (torneio.between_rounds || !activeRound?.matches?.length),
    ),
  });

  useEffect(() => {
    if (torneio?.status === "draft" && isStaff) {
      searchRef.current?.focus();
    }
  }, [torneio?.status, eventId, isStaff]);

  useEffect(() => {
    if (!playerAddedFlash) return;
    const t = window.setTimeout(() => setPlayerAddedFlash(false), 2000);
    return () => window.clearTimeout(t);
  }, [playerAddedFlash]);

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(userSearch.trim()), 280);
    return () => window.clearTimeout(t);
  }, [userSearch]);

  useEffect(() => {
    if (debouncedSearch.length < 2) {
      setUserHits([]);
      setSearchDone(false);
      return;
    }
    let cancelled = false;
    setSearchDone(false);
    api
      .searchUsers(debouncedSearch)
      .then((rows) => {
        if (cancelled) return;
        setUserHits(rows);
        setSearchDone(true);
      })
      .catch((e) => {
        if (cancelled) return;
        setError((e as Error).message);
        setUserHits([]);
        setSearchDone(true);
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedSearch]);

  const focusSearchField = () => {
    requestAnimationFrame(() => searchRef.current?.focus());
  };

  const addPlayer = useMutation({
    mutationFn: async (payload: {
      name: string;
      seed?: number;
      email?: string;
      phone?: string;
      create_account?: boolean;
      user_id?: number;
    }) =>
      api.addJogador(eventId, payload.name, payload.seed, {
        email: payload.email,
        phone: payload.phone,
        create_account: payload.create_account,
        user_id: payload.user_id,
      }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      setPlayerName("");
      setPlayerSeed("");
      setPlayerEmail("");
      setPlayerPhone("");
      setShowCreateIncomplete(false);
      setUserSearch("");
      setDebouncedSearch("");
      setUserHits([]);
      setSearchDone(false);
      setError("");
      setPlayerAddedFlash(true);
      focusSearchField();
    },
    onError: (e) => {
      setError((e as Error).message);
      focusSearchField();
      requestAnimationFrame(() =>
        formErrorRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }),
      );
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
    onSuccess: (t) => {
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      navigate(`/torneios/${eventId}/rodadas/${t.current_round}`);
    },
    onError: (e) => setError((e as Error).message),
  });

  const checkIn = useMutation({
    mutationFn: (pid: number) => api.checkInPlayer(eventId, pid),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["torneio", eventId] }),
    onError: (e) => setError((e as Error).message),
  });

  const toggleRegistration = useMutation({
    mutationFn: (open: boolean) => api.updateTorneio(eventId, { registration_open: open }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["torneio", eventId] }),
    onError: (e) => setError((e as Error).message),
  });

  const selfRegister = useMutation({
    mutationFn: () => api.selfRegister(eventId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      qc.invalidateQueries({ queryKey: ["torneios"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const deleteEvent = useMutation({
    mutationFn: () => api.deleteTorneio(eventId),
    onSuccess: () => {
      navigate("/torneios");
    },
    onError: (e) => setError((e as Error).message),
  });

  const iniciarProxima = useMutation({
    mutationFn: () => api.iniciarProximaRodada(eventId),
    onSuccess: (t) => {
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      navigate(`/torneios/${eventId}/rodadas/${t.current_round}`);
    },
    onError: (e) => setError((e as Error).message),
  });

  const reabrirRodada = useMutation({
    mutationFn: () => api.reabrirRodada(eventId),
    onSuccess: (t) => {
      setReabrirModalOpen(false);
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      navigate(`/torneios/${eventId}/rodadas/${t.current_round}`);
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
      navigate(`/torneios/${eventId}/resultado`);
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

  if (isGuest && torneio?.status === "finished") {
    return <Navigate to={`/torneios/${eventId}/resultado`} replace />;
  }

  if (torneioLoading || !meFetched) return <p>Carregando...</p>;
  if (isError || !torneio) {
    return (
      <p className="error">
        {(torneioError instanceof Error ? torneioError.message : null) || "Torneio não encontrado."}
      </p>
    );
  }

  const isDraft = torneio.status === "draft";
  const isManual = torneio.pairing_mode === "manual";
  const isRunning = torneio.status === "running";
  const isFinished = torneio.status === "finished";
  const hasActiveRound = isRunning && !torneio.between_rounds && torneio.current_round > 0;
  const isEnrolled = Boolean(me && torneio.players?.some((p) => p.user_id === me.id));
  const isSignupVitrine =
    isDraft && Boolean(torneio.registration_open) && !isStaff && !isEnrolled;
  const activePlayers =
    torneio.players?.filter((p) => !p.dropped_at).map((p) => ({ id: p.id, name: p.name })) ?? [];

  const draftPlayers = torneio.players ?? [];
  const missingSeedPlayers = playersMissingSeed(draftPlayers);
  const missingSeedIds = new Set(missingSeedPlayers.map((p) => p.id));
  const seedsIncomplete = missingSeedPlayers.length > 0;
  const seedRequired = draftPlayers.some((p) => p.seed != null);
  const seedErrorMessage = seedRequirementMessage(missingSeedPlayers.map((p) => p.name));
  const pendingCount = torneio.pending_checkins ?? 0;
  const playerCount = torneio.players?.length ?? 0;
  const canStart =
    isDraft &&
    isStaff &&
    !isManual &&
    playerCount >= 4 &&
    !seedsIncomplete &&
    pendingCount === 0 &&
    !iniciar.isPending;
  const canRegisterPlacements =
    isDraft &&
    isStaff &&
    isManual &&
    playerCount >= 1 &&
    pendingCount === 0;
  const placementBlockReason = pendingCount > 0
    ? "Faça check-in de todas as inscrições pendentes"
    : playerCount < 1
      ? "Adicione ao menos um jogador com check-in"
      : undefined;
  const startBlockReason = seedsIncomplete
    ? "Corrija o seeding parcial antes de iniciar"
    : pendingCount > 0
      ? "Faça check-in de todas as inscrições pendentes"
      : playerCount < 4
        ? "Mínimo de 4 jogadores para iniciar"
        : undefined;

  const canCreateIncomplete =
    Boolean(playerName.trim()) &&
    Boolean(playerEmail.trim()) &&
    Boolean(playerPhone.trim()) &&
    !addPlayer.isPending &&
    !(seedRequired && !playerSeed.trim());

  const submitIncomplete = () => {
    if (!canCreateIncomplete) return;
    if (!isValidPhoneInput(playerPhone)) {
      setError(`Celular inválido. ${PHONE_HINT}`);
      requestAnimationFrame(() =>
        formErrorRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }),
      );
      return;
    }
    addPlayer.mutate({
      name: playerName.trim(),
      seed: playerSeed.trim() ? parseInt(playerSeed, 10) : undefined,
      email: playerEmail.trim(),
      phone: playerPhone.trim(),
      create_account: true,
    });
  };

  const clearCreateForm = () => {
    setPlayerName("");
    setPlayerSeed("");
    setPlayerEmail("");
    setPlayerPhone("");
    setShowCreateIncomplete(false);
    setError("");
  };

  const openCreateIncomplete = () => {
    setShowCreateIncomplete(true);
    setPlayerName(userSearch.trim() || playerName);
    requestAnimationFrame(() => playerNameRef.current?.focus());
  };

  const handleCreateKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      clearCreateForm();
      focusSearchField();
      return;
    }
    if (e.key !== "Enter") return;
    e.preventDefault();
    submitIncomplete();
  };

  const reabrirMessage = hasActiveRound
    ? `Reabrir rodada ${torneio.current_round - 1}? A rodada ${torneio.current_round} será removida e o pairing refeito ao avançar.`
    : `Reabrir rodada ${torneio.completed_rounds} para corrigir resultados?`;

  // Staff with an active round go straight to pairings (no intermediate hub).
  if (isStaff && hasActiveRound) {
    return <Navigate to={`/torneios/${eventId}/rodadas/${torneio.current_round}`} replace />;
  }

  if (isSignupVitrine) {
    const next = encodeURIComponent(`/torneios/${eventId}`);
    return (
      <div>
        <Link to="/torneios">← Torneios</Link>
        <h1>{torneio.name}</h1>
        <p>
          {torneio.event_date} · {torneio.format === "swiss" ? "Suíço" : "Eliminatória"} ·{" "}
          <span className="badge">inscrição aberta</span>
        </p>
        <ul style={{ margin: "1rem 0", paddingLeft: "1.25rem", lineHeight: 1.7 }}>
          <li>
            Formato: {torneio.format === "swiss" ? "Suíço" : "Eliminatória simples"}
            {torneio.max_rounds != null ? ` · até ${torneio.max_rounds} rodadas` : ""}
          </li>
          <li>Best of: {torneio.best_of}</li>
          <li>Inscrição: R$ {torneio.entry_fee}</li>
          <li>Inscritos: {torneio.player_count}</li>
        </ul>
        {isGuest ? (
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <Link className="primary" to={`/?auth=login&next=${next}`}>
              Entrar para se inscrever
            </Link>
            <Link className="secondary" to={`/?auth=register&next=${next}`}>
              Criar conta
            </Link>
          </div>
        ) : (
          <>
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            <button
              className="primary"
              type="button"
              onClick={() => selfRegister.mutate()}
              disabled={selfRegister.isPending}
            >
              {selfRegister.isPending ? "Inscrevendo…" : "Inscrever-me neste torneio"}
            </button>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="torneio-manage">
      <header className="torneio-manage-header">
        <div className="torneio-manage-header-main">
          <Link to="/torneios" className="torneio-back">
            ← Torneios
          </Link>
          <div className="torneio-manage-title-row">
            <h1>{torneio.name}</h1>
            {isAdmin && (
              <div className="torneio-overflow">
                <button
                  type="button"
                  className="secondary torneio-overflow-btn"
                  aria-expanded={adminMenuOpen}
                  aria-haspopup="menu"
                  onClick={() => setAdminMenuOpen((v) => !v)}
                >
                  ⋯
                </button>
                {adminMenuOpen && (
                  <div className="torneio-overflow-menu" role="menu">
                    <button
                      type="button"
                      role="menuitem"
                      className="danger-text"
                      onClick={() => {
                        setAdminMenuOpen(false);
                        setDeleteNameInput("");
                        setDeleteConfirmOpen(true);
                      }}
                    >
                      Excluir torneio…
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
          <p className="torneio-manage-meta">
            {torneio.event_date}
            {torneio.start_time ? ` · ${torneio.start_time}` : ""} ·{" "}
            {torneio.format === "swiss" ? "Suíço" : "Eliminatória"}
            {torneio.tcg_game ? ` · ${torneio.tcg_game.name}` : ""} ·{" "}
            <span className="badge">{torneio.status}</span>
            {torneio.source === "external" && <span className="badge">externo</span>}
            {isManual && <span className="badge">sem rodadas</span>}
          </p>
          {isDraft && isStaff && (
            <Switch
              className="torneio-reg-toggle"
              checked={Boolean(torneio.registration_open)}
              onChange={(checked) => toggleRegistration.mutate(checked)}
              disabled={toggleRegistration.isPending}
            >
              Inscrições abertas para jogadores
            </Switch>
          )}
        </div>
        {isDraft && isStaff && !isManual && (
          <div className="torneio-manage-primary">
            <button
              className="primary"
              type="button"
              onClick={handleIniciar}
              disabled={!canStart}
              title={startBlockReason}
            >
              {iniciar.isPending ? "Iniciando…" : "Iniciar torneio"}
            </button>
            {!canStart && startBlockReason && (
              <p className="field-hint">{startBlockReason}</p>
            )}
          </div>
        )}
        {isDraft && isStaff && isManual && (
          <div className="torneio-manage-primary">
            <Link
              className="primary"
              to={`/torneios/${eventId}/colocacoes`}
              aria-disabled={!canRegisterPlacements}
              style={!canRegisterPlacements ? { pointerEvents: "none", opacity: 0.6 } : undefined}
              title={placementBlockReason}
            >
              Registrar colocações
            </Link>
            {!canRegisterPlacements && placementBlockReason && (
              <p className="field-hint">{placementBlockReason}</p>
            )}
          </div>
        )}
        {isRunning && torneio.between_rounds && isStaff && (
          <div className="torneio-manage-primary">
            {torneio.can_start_next_round && (
              <button
                ref={nextRoundBtnRef}
                className="primary"
                type="button"
                onClick={() => iniciarProxima.mutate()}
                disabled={iniciarProxima.isPending}
              >
                {iniciarProxima.isPending
                  ? "Iniciando…"
                  : `Iniciar rodada ${(torneio.completed_rounds ?? 0) + 1}`}
              </button>
            )}
            {torneio.can_finalize && !torneio.can_start_next_round && (
              <button
                ref={finalizeBtnRef}
                className="primary"
                type="button"
                onClick={() => setFinalizarModalOpen(true)}
                disabled={finalizar.isPending}
              >
                {finalizar.isPending ? "Finalizando…" : "Finalizar torneio"}
              </button>
            )}
          </div>
        )}
      </header>

      <div className="stepper">
        <span className={isDraft ? "active" : ""}>Jogadores</span>
        <span className={isRunning ? "active" : ""}>Rodadas</span>
        <span className={isFinished ? "active" : ""}>Resultado</span>
      </div>

      {error && (
        <p ref={formErrorRef} className="error" role="alert">
          {error}
        </p>
      )}
      {torneio.config_warnings?.map((w) => (
        <p key={w} className="warning" role="status">
          {w}
        </p>
      ))}

      {isDraft && pendingCount > 0 && (
        <p className="warning" role="status">
          {pendingCount} inscrição(ões) pendente(s) de check-in — o torneio não inicia até confirmar
          presença.
        </p>
      )}

      {isDraft && me && torneio.registration_open && !isEnrolled && isStaff && (
        <div className="torneio-self-enroll">
          <button
            className="secondary"
            type="button"
            onClick={() => selfRegister.mutate()}
            disabled={selfRegister.isPending}
          >
            {selfRegister.isPending ? "Inscrevendo…" : "Inscrever-me neste torneio"}
          </button>
        </div>
      )}

      {isDraft && isStaff && (
        <TorneioDraftEditPanel eventId={eventId} torneio={torneio} />
      )}

      {isDraft && (
        <div className="torneio-draft-layout">
          <section className="torneio-panel">
            <div className="torneio-panel-head">
              <h2>
                Inscritos{" "}
                <span className="torneio-count">
                  {playerCount}
                  {pendingCount > 0 ? ` · ${pendingCount} pendente` : ""}
                </span>
              </h2>
            </div>
            {isStaff && torneio.format === "single_elimination" && !isManual && (
              <div className="torneio-se-block">
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
                  <>
                    <p className="warning" style={{ marginBottom: "0.5rem" }}>
                      Opções SE alteradas — salve antes de iniciar. Bo global atual:{" "}
                      {torneio.best_of}.
                    </p>
                    <button
                      className="secondary"
                      style={{ marginBottom: "1rem" }}
                      onClick={() => saveSeOptions.mutate()}
                      disabled={saveSeOptions.isPending}
                    >
                      Salvar opções SE
                    </button>
                  </>
                )}
              </div>
            )}
            {torneio.max_rounds != null && playerCount >= 4 && (
              <p className="warning">
                Recomendado: {torneio.recommended_rounds ?? "—"} rodadas para {playerCount} jogadores
                {torneio.max_rounds < (torneio.recommended_rounds ?? 0) &&
                  ` (configurado: ${torneio.max_rounds})`}
              </p>
            )}
            {seedsIncomplete && !isManual && (
              <p className="error" role="alert">
                {seedErrorMessage} Remova e cadastre de novo com seed, ou remova os seeds existentes.
              </p>
            )}
            {playerCount === 0 ? (
              <p className="muted torneio-empty-roster">Nenhum inscrito ainda.</p>
            ) : (
              <ul className="player-draft-list">
                {torneio.players?.map((p) => {
                  const needsSeed = missingSeedIds.has(p.id);
                  return (
                    <li
                      key={p.id}
                      className={
                        needsSeed ? "player-row player-row-seed-missing" : "player-row"
                      }
                    >
                      <div className="player-row-main">
                        <span className="player-row-name">{p.name}</span>
                        <span className="player-row-meta">
                          {p.seed != null
                            ? `Seed ${p.seed}`
                            : needsSeed
                              ? "Falta seed"
                              : null}
                          {p.attendance === "pending" && (
                            <span className="badge badge-warn">pendente</span>
                          )}
                          {p.attendance === "checked_in" && (
                            <span className="badge badge-ok">check-in</span>
                          )}
                        </span>
                      </div>
                      <div className="player-row-actions">
                        {isStaff && p.attendance === "pending" && (
                          <button
                            className="secondary"
                            type="button"
                            onClick={() => checkIn.mutate(p.id)}
                            disabled={checkIn.isPending}
                          >
                            Check-in
                          </button>
                        )}
                        {isStaff && (
                          <button
                            className="secondary"
                            type="button"
                            onClick={() => setRemoveTarget({ id: p.id, name: p.name })}
                          >
                            Remover
                          </button>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

          {isStaff && (
            <section className="torneio-panel torneio-add-panel">
              <div className="torneio-panel-head">
                <h2>Adicionar inscrito</h2>
                <p className="field-hint">
                  Busque uma conta. Se não existir, crie incomplete (e-mail + celular).
                </p>
              </div>
              <div className="form-row">
                <label htmlFor="user-search">Buscar jogador</label>
                <input
                  id="user-search"
                  ref={searchRef}
                  value={userSearch}
                  onChange={(e) => {
                    setUserSearch(e.target.value);
                    setShowCreateIncomplete(false);
                  }}
                  placeholder="Nome, e-mail ou celular"
                  autoComplete="off"
                />
              </div>

              {debouncedSearch.length >= 2 && userHits.length > 0 && (
                <ul className="torneio-search-hits">
                  {userHits.map((u) => (
                    <li key={u.id} className="player-row">
                      <div className="player-row-main">
                        <span className="player-row-name">{u.display_name}</span>
                        <span className="player-row-meta muted">
                          {[u.email, u.phone].filter(Boolean).join(" · ")}
                        </span>
                      </div>
                      <button
                        className="primary"
                        type="button"
                        disabled={addPlayer.isPending}
                        onClick={() =>
                          addPlayer.mutate({
                            name: u.display_name,
                            user_id: u.id,
                            seed: playerSeed.trim()
                              ? parseInt(playerSeed, 10)
                              : undefined,
                          })
                        }
                      >
                        Inscrever
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              {debouncedSearch.length >= 2 && searchDone && userHits.length === 0 && (
                <div className="torneio-create-prompt">
                  <p>Nenhuma conta encontrada para “{debouncedSearch}”.</p>
                  {!showCreateIncomplete ? (
                    <button
                      type="button"
                      className="secondary"
                      onClick={openCreateIncomplete}
                    >
                      Criar conta incompleta
                    </button>
                  ) : null}
                </div>
              )}

              {showCreateIncomplete && (
                <div className="torneio-create-form">
                  <h3>Nova conta incompleta</h3>
                  <div className="form-row">
                    <label htmlFor="player-name">Nome</label>
                    <input
                      id="player-name"
                      ref={playerNameRef}
                      value={playerName}
                      onChange={(e) => setPlayerName(e.target.value)}
                      onKeyDown={handleCreateKeyDown}
                      disabled={addPlayer.isPending}
                    />
                  </div>
                  <div className="form-row">
                    <label htmlFor="player-email">E-mail</label>
                    <input
                      id="player-email"
                      type="email"
                      value={playerEmail}
                      onChange={(e) => setPlayerEmail(e.target.value)}
                      onKeyDown={handleCreateKeyDown}
                      required
                      disabled={addPlayer.isPending}
                    />
                  </div>
                  <div className="form-row">
                    <label htmlFor="player-phone">Celular</label>
                    <input
                      id="player-phone"
                      type="tel"
                      inputMode="numeric"
                      autoComplete="tel"
                      placeholder="11987654321"
                      value={playerPhone}
                      onChange={(e) => {
                        setPlayerPhone(e.target.value);
                        if (error) setError("");
                      }}
                      onKeyDown={handleCreateKeyDown}
                      required
                      disabled={addPlayer.isPending}
                      aria-describedby="player-phone-hint"
                    />
                    <p id="player-phone-hint" className="field-hint">
                      {PHONE_HINT}
                    </p>
                  </div>
                  <details className="torneio-advanced" open={seedRequired || undefined}>
                    <summary>Opções avançadas</summary>
                    <div className="form-row">
                      <label htmlFor="player-seed">
                        Seed {seedRequired ? "(obrigatório)" : "(opcional)"}
                      </label>
                      <input
                        id="player-seed"
                        ref={playerSeedRef}
                        type="number"
                        value={playerSeed}
                        onChange={(e) => setPlayerSeed(e.target.value)}
                        onKeyDown={handleCreateKeyDown}
                        className={
                          seedRequired && !playerSeed.trim() ? "input-invalid" : undefined
                        }
                        disabled={addPlayer.isPending}
                      />
                    </div>
                  </details>
                  <div className="torneio-create-actions">
                    <button
                      className="primary"
                      type="button"
                      onClick={submitIncomplete}
                      disabled={!canCreateIncomplete}
                    >
                      {addPlayer.isPending ? "Criando…" : "Criar e inscrever"}
                    </button>
                    <button
                      className="secondary"
                      type="button"
                      onClick={clearCreateForm}
                      disabled={addPlayer.isPending}
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}

              {seedRequired && !showCreateIncomplete && (
                <details className="torneio-advanced" open>
                  <summary>Seed (obrigatório — seeding já iniciado)</summary>
                  <div className="form-row">
                    <label htmlFor="enroll-seed">Seed ao inscrever conta existente</label>
                    <input
                      id="enroll-seed"
                      type="number"
                      value={playerSeed}
                      onChange={(e) => setPlayerSeed(e.target.value)}
                    />
                  </div>
                </details>
              )}

              {playerAddedFlash && (
                <div className="save-feedback success" role="status" aria-live="polite">
                  Inscrito adicionado
                </div>
              )}
            </section>
          )}
        </div>
      )}

      {isRunning && !isStaff && (
        <div style={{ marginTop: "1rem" }}>
          <p>
            {hasActiveRound
              ? `Rodada ${torneio.current_round} / ${torneio.max_rounds}`
              : torneio.between_rounds
                ? `Rodada ${torneio.completed_rounds} concluída — aguardando próxima`
                : "Torneio em andamento"}
          </p>
          {hasActiveRound && activeRound?.matches && activeRound.matches.length > 0 ? (
            <RoundMatchesTable
              title={`Pairings — rodada ${torneio.current_round}`}
              matches={activeRound.matches}
            />
          ) : (
            <>
              {torneio.between_rounds && lastCompletedRound && (
                <RoundMatchesTable
                  title={`Resultados — rodada ${lastCompletedRound.number}`}
                  matches={lastCompletedRound.matches}
                />
              )}
              {liveClassificacao && (
                <>
                  <h2 style={{ marginTop: "1.5rem" }}>Classificação atual</h2>
                  <table>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Jogador</th>
                        <th>Pts</th>
                        <th>OMW%</th>
                        <th>GW%</th>
                        <th>OGW%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {liveClassificacao.standings.map((s) => (
                        <tr key={s.player_id}>
                          <td>{s.rank_label ?? s.rank}</td>
                          <td>{s.name}</td>
                          <td>{s.is_drop ? "—" : s.points}</td>
                          <td>{s.is_drop ? "—" : `${(s.omw * 100).toFixed(1)}%`}</td>
                          <td>{s.is_drop ? "—" : `${(s.gw * 100).toFixed(1)}%`}</td>
                          <td>{s.is_drop ? "—" : `${(s.ogw * 100).toFixed(1)}%`}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
              {!liveClassificacao && !(torneio.between_rounds && lastCompletedRound) && (
                <p style={{ opacity: 0.85 }}>Aguardando pairings da rodada.</p>
              )}
            </>
          )}
        </div>
      )}

      {isRunning && torneio.between_rounds && isStaff && (
        <section className="entre-rodadas">
          <div className="entre-rodadas-head">
            <div>
              <h2>Entre rodadas</h2>
              <p className="field-hint">
                Rodada {torneio.completed_rounds} concluída
                {torneio.can_start_next_round
                  ? ` · próxima: ${(torneio.completed_rounds ?? 0) + 1}`
                  : torneio.can_finalize
                    ? " · todas as rodadas concluídas"
                    : ""}
              </p>
            </div>
            <div className="entre-rodadas-secondary">
              {torneio.can_reopen_round && (
                <button
                  className="secondary"
                  type="button"
                  onClick={() => setReabrirModalOpen(true)}
                  disabled={reabrirRodada.isPending}
                >
                  Reabrir rodada {torneio.completed_rounds}
                </button>
              )}
              {torneio.can_finalize && torneio.can_start_next_round && (
                <button
                  ref={finalizeBtnRef}
                  className="secondary"
                  type="button"
                  onClick={() => setFinalizarModalOpen(true)}
                  disabled={finalizar.isPending}
                >
                  Finalizar torneio
                </button>
              )}
            </div>
          </div>

          {lastCompletedRound && (
            <div className="entre-rodadas-summary">
              <h3>Resumo — rodada {lastCompletedRound.number}</h3>
              <p className="field-hint">
                Confira os resultados antes de avançar. Corrija com Reabrir se necessário.
              </p>
              <div className="match-card-list match-card-list-compact">
                {lastCompletedRound.matches.map((m, idx) => (
                  <article key={m.id} className="match-card match-card-readonly">
                    <div className="match-scoreline-wrap">
                      <div className="match-card-meta">
                        <span className="match-card-num">Mesa {idx + 1}</span>
                        {m.is_bye && <span className="badge">BYE</span>}
                        {m.is_walkover && <span className="badge">WO</span>}
                        {m.had_rematch && <span className="badge badge-rematch">Rematch</span>}
                        {m.is_third_place && <span className="badge">3º–4º</span>}
                      </div>
                      {m.is_bye ? (
                        <div className="match-scoreline match-scoreline-bye">
                          <span className="match-cell-name">{m.player1_name}</span>
                        </div>
                      ) : (
                        <div className="match-scoreline">
                          <span className="match-cell-name match-scoreline-p1">{m.player1_name}</span>
                          <span className="match-scoreline-score">
                            {m.scores_submitted || m.is_walkover ? m.score_p1 : "—"}
                          </span>
                          <span className="match-scoreline-vs" aria-hidden>
                            ×
                          </span>
                          <span className="match-scoreline-score">
                            {m.scores_submitted || m.is_walkover ? m.score_p2 : "—"}
                          </span>
                          <span className="match-cell-name match-scoreline-p2">
                            {m.player2_name ?? "—"}
                          </span>
                        </div>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          )}

          {activePlayers.length > 0 && (
            <div className="entre-rodadas-roster">
              <div className="entre-rodadas-roster-head">
                <h3>
                  Ainda no torneio <span className="torneio-count">{activePlayers.length}</span>
                </h3>
                <button
                  className="secondary"
                  type="button"
                  onClick={() => setDropModalOpen(true)}
                >
                  Registrar drop…
                </button>
              </div>
              <p className="field-hint">
                Drop entre rodadas remove o jogador sem WO na partida atual.
              </p>
              <ul className="entre-rodadas-chips">
                {activePlayers.map((p) => (
                  <li key={p.id} className="entre-rodadas-chip">
                    {p.name}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
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
        requireNameConfirm
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

      <Modal
        open={deleteConfirmOpen}
        title="Excluir torneio"
        onClose={() => setDeleteConfirmOpen(false)}
        footer={
          <>
            <button
              type="button"
              className="secondary"
              onClick={() => setDeleteConfirmOpen(false)}
              disabled={deleteEvent.isPending}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="danger"
              disabled={
                deleteEvent.isPending || deleteNameInput.trim() !== torneio.name
              }
              onClick={() => deleteEvent.mutate()}
            >
              Excluir definitivamente
            </button>
          </>
        }
      >
        <p className="modal-message">
          Esta ação remove o evento, rodadas, partidas e FP deste torneio. Digite o nome exato para
          confirmar: <strong>{torneio.name}</strong>
        </p>
        <div className="form-row">
          <label htmlFor="delete-name">Nome do torneio</label>
          <input
            id="delete-name"
            value={deleteNameInput}
            onChange={(e) => setDeleteNameInput(e.target.value)}
            autoComplete="off"
          />
        </div>
      </Modal>
    </div>
  );
}
