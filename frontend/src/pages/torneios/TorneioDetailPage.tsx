import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type ClipboardEvent, type KeyboardEvent } from "react";
import { Link, Navigate, useParams } from "react-router-dom";

import { ConfirmModal } from "../../components/ConfirmModal";
import { Modal } from "../../components/Modal";
import { PlayerPickerModal } from "../../components/PlayerPickerModal";
import { RoundMatchesTable } from "../../components/RoundMatchesTable";
import { SeFormatOptions, type SeBoConfig } from "../../components/SeFormatOptions";
import { api } from "../../api/client";
import { parsePastedNames } from "../../utils/pasteNames";
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
  const qc = useQueryClient();
  const { data: me, isFetched: meFetched } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const isStaff = me && (me.role === "admin" || me.role === "staff");
  const isAdmin = me?.role === "admin";
  const isGuest = meFetched && !me;
  const [playerName, setPlayerName] = useState("");
  const [playerSeed, setPlayerSeed] = useState("");
  const [playerEmail, setPlayerEmail] = useState("");
  const [playerPhone, setPlayerPhone] = useState("");
  const [createAccount, setCreateAccount] = useState(false);
  const [userSearch, setUserSearch] = useState("");
  const [userHits, setUserHits] = useState<
    Array<{ id: number; display_name: string; email?: string; phone?: string | null }>
  >([]);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleteNameInput, setDeleteNameInput] = useState("");
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
      playerNameRef.current?.focus();
    }
  }, [torneio?.status, eventId, isStaff]);

  useEffect(() => {
    if (!playerAddedFlash) return;
    const t = window.setTimeout(() => setPlayerAddedFlash(false), 2000);
    return () => window.clearTimeout(t);
  }, [playerAddedFlash]);

  const focusNameField = () => {
    requestAnimationFrame(() => playerNameRef.current?.focus());
  };

  const addPlayer = useMutation({
    mutationFn: async (payload: {
      names: string[];
      seed?: number;
      email?: string;
      phone?: string;
      create_account?: boolean;
      user_id?: number;
    }) => {
      for (const name of payload.names) {
        await api.addJogador(eventId, name, payload.seed, {
          email: payload.email,
          phone: payload.phone,
          create_account: payload.create_account,
          user_id: payload.user_id,
        });
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      setPlayerName("");
      setPlayerSeed("");
      setPlayerEmail("");
      setPlayerPhone("");
      setCreateAccount(false);
      setError("");
      setPlayerAddedFlash(true);
      focusNameField();
    },
    onError: (e) => {
      setError((e as Error).message);
      focusNameField();
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["torneio", eventId] }),
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

  const searchUsers = useMutation({
    mutationFn: (q: string) => api.searchUsers(q),
    onSuccess: (rows) => setUserHits(rows),
    onError: (e) => setError((e as Error).message),
  });

  const deleteEvent = useMutation({
    mutationFn: () => api.deleteTorneio(eventId),
    onSuccess: () => {
      window.location.href = "/torneios";
    },
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
  const canSubmitPlayer =
    Boolean(playerName.trim()) &&
    !addPlayer.isPending &&
    !(seedRequired && !playerSeed.trim()) &&
    (!createAccount || (Boolean(playerEmail.trim()) && Boolean(playerPhone.trim())));

  const submitPlayer = () => {
    if (!canSubmitPlayer) return;
    if (createAccount && !isValidPhoneInput(playerPhone)) {
      setError(`Celular inválido. ${PHONE_HINT}`);
      requestAnimationFrame(() =>
        formErrorRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }),
      );
      return;
    }
    addPlayer.mutate({
      names: [playerName.trim()],
      seed: playerSeed.trim() ? parseInt(playerSeed, 10) : undefined,
      email: createAccount ? playerEmail.trim() : undefined,
      phone: createAccount ? playerPhone.trim() : undefined,
      create_account: createAccount || undefined,
    });
  };

  const clearPlayerForm = () => {
    setPlayerName("");
    setPlayerSeed("");
    setPlayerEmail("");
    setPlayerPhone("");
    setCreateAccount(false);
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
    <div>
      <h1>{torneio.name}</h1>
      <p>
        {torneio.event_date} · {torneio.format === "swiss" ? "Suíço" : "Eliminatória"} ·{" "}
        <span className="badge">{torneio.status}</span>
        {torneio.source === "external" && <span className="badge"> externo</span>}
      </p>
      {isAdmin && (
        <div style={{ marginBottom: "1rem" }}>
          <button
            className="secondary"
            type="button"
            onClick={() => {
              setDeleteNameInput("");
              setDeleteConfirmOpen(true);
            }}
          >
            Excluir torneio…
          </button>
        </div>
      )}

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

      {isDraft && (torneio.pending_checkins ?? 0) > 0 && (
        <p className="warning" role="status">
          {torneio.pending_checkins} inscrição(ões) pendente(s) de check-in — o torneio não inicia
          até confirmar presença.
        </p>
      )}

      {isDraft && me && torneio.registration_open && !isEnrolled && isStaff && (
        <div style={{ marginBottom: "1rem" }}>
          <button
            className="primary"
            type="button"
            onClick={() => selfRegister.mutate()}
            disabled={selfRegister.isPending}
          >
            Inscrever-me neste torneio
          </button>
        </div>
      )}

      {isDraft && isStaff && (
        <div className="form-row" style={{ marginBottom: "1rem" }}>
          <label>
            <input
              type="checkbox"
              checked={Boolean(torneio.registration_open)}
              onChange={(e) => toggleRegistration.mutate(e.target.checked)}
              disabled={toggleRegistration.isPending}
            />{" "}
            Inscrições abertas (jogadores logados podem se inscrever)
          </label>
        </div>
      )}

      {isDraft && (
        <>
          <h2>Jogadores ({torneio.players?.length ?? 0})</h2>
          {isStaff && torneio.format === "single_elimination" && (
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
                    {p.attendance === "pending" ? " · pendente" : ""}
                  </span>{" "}
                  {isStaff && p.attendance === "pending" && (
                    <button
                      className="secondary"
                      type="button"
                      onClick={() => checkIn.mutate(p.id)}
                      disabled={checkIn.isPending}
                    >
                      Check-in
                    </button>
                  )}{" "}
                  {isStaff && (
                    <button
                      className="secondary"
                      onClick={() => setRemoveTarget({ id: p.id, name: p.name })}
                    >
                      Remover
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
          {isStaff && (
            <>
              <div className="card" style={{ marginBottom: "1rem" }}>
                <h3>Inscrever conta existente</h3>
                <div className="form-row">
                  <label htmlFor="user-search">Buscar (nome, e-mail ou celular)</label>
                  <input
                    id="user-search"
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        if (userSearch.trim().length >= 1) searchUsers.mutate(userSearch.trim());
                      }
                    }}
                  />
                </div>
                <button
                  className="secondary"
                  type="button"
                  disabled={userSearch.trim().length < 1 || searchUsers.isPending}
                  onClick={() => searchUsers.mutate(userSearch.trim())}
                >
                  Buscar
                </button>
                {userHits.length > 0 && (
                  <ul style={{ marginTop: "0.75rem" }}>
                    {userHits.map((u) => (
                      <li key={u.id} className="player-row">
                        <span>
                          {u.display_name}
                          {u.email ? ` · ${u.email}` : ""}
                          {u.phone ? ` · ${u.phone}` : ""}
                        </span>{" "}
                        <button
                          className="secondary"
                          type="button"
                          disabled={addPlayer.isPending}
                          onClick={() =>
                            addPlayer.mutate({
                              names: [u.display_name],
                              user_id: u.id,
                            })
                          }
                        >
                          Inscrever
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="form-row">
                <label htmlFor="player-name">Nome (walk-in / nova incomplete)</label>
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
              <div className="form-row">
                <label>
                  <input
                    type="checkbox"
                    checked={createAccount}
                    onChange={(e) => setCreateAccount(e.target.checked)}
                    disabled={addPlayer.isPending}
                  />{" "}
                  Criar conta incompleta (e-mail + celular → convite depois)
                </label>
              </div>
              {createAccount && (
                <>
                  <div className="form-row">
                    <label htmlFor="player-email">E-mail</label>
                    <input
                      id="player-email"
                      type="email"
                      value={playerEmail}
                      onChange={(e) => setPlayerEmail(e.target.value)}
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
                      required
                      disabled={addPlayer.isPending}
                      aria-describedby="player-phone-hint"
                    />
                    <p id="player-phone-hint" style={{ fontSize: "0.8rem", opacity: 0.8, margin: "0.25rem 0 0" }}>
                      {PHONE_HINT}
                    </p>
                  </div>
                </>
              )}
              {error && (
                <p ref={formErrorRef} className="error" role="alert" style={{ marginTop: "0.75rem" }}>
                  {error}
                </p>
              )}
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
                    (torneio.pending_checkins ?? 0) > 0 ||
                    iniciar.isPending
                  }
                  title={
                    seedsIncomplete
                      ? "Corrija o seeding parcial antes de iniciar"
                      : (torneio.pending_checkins ?? 0) > 0
                        ? "Faça check-in de todas as inscrições pendentes"
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
        </>
      )}

      {isRunning && hasActiveRound && isStaff && (
        <>
          <p>
            Rodada ativa: {torneio.current_round} / {torneio.max_rounds}
          </p>
          <Link
            to={`/torneios/${eventId}/rodadas/${torneio.current_round}`}
            className="primary"
            style={{
              display: "inline-block",
              marginTop: "1rem",
              padding: "0.6rem 1.25rem",
              borderRadius: 999,
            }}
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
