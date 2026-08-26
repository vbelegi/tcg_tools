import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";

import { ConfirmModal } from "../../components/ConfirmModal";
import { MatchBadges } from "../../components/MatchBadges";
import { PlayerPickerModal } from "../../components/PlayerPickerModal";
import { api } from "../../api/client";
import type { Match } from "../../api/types";
import { formatPlayerRecord, playerRecordTitle, type PlayerRecordWld } from "../../utils/playerRecord";
import { incompleteMatches, isMatchIncomplete, matchSummaryLabel } from "../../utils/matches";
import { scoreOptionLabel, validScoresForPlayer } from "../../utils/scores";

type ScoreDraft = { p1: string; p2: string };

function getMatchScores(
  matchId: number,
  match: Match,
  drafts: Record<number, ScoreDraft>,
): ScoreDraft {
  const draft = drafts[matchId];
  if (draft) return draft;
  if (match.scores_submitted) {
    return { p1: String(match.score_p1), p2: String(match.score_p2) };
  }
  return { p1: "", p2: "" };
}

function ScoreSelect({
  value,
  options,
  bestOf,
  allowDraw,
  onChange,
  disabled,
  label,
  matchId,
  side,
}: {
  value: string;
  options: number[];
  bestOf: number;
  allowDraw: boolean;
  onChange: (v: string) => void;
  disabled?: boolean;
  label: string;
  matchId: number;
  side: "p1" | "p2";
}) {
  const numericValue = value === "" ? null : Number(value);
  const optionSet = new Set(options);
  if (numericValue !== null && !Number.isNaN(numericValue) && !optionSet.has(numericValue)) {
    optionSet.add(numericValue);
  }
  const sorted = Array.from(optionSet).sort((a, b) => a - b);

  return (
    <select
      className="score-select score-select-lg"
      aria-label={label}
      title={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      data-match-id={matchId}
      data-score-side={side}
    >
      <option value="">—</option>
      {sorted.map((n) => (
        <option key={n} value={String(n)} title={scoreOptionLabel(n, bestOf, allowDraw)}>
          {n}
        </option>
      ))}
    </select>
  );
}

function PlayerNameWithRecord({
  name,
  record,
}: {
  name: string;
  record: PlayerRecordWld | undefined;
}) {
  return (
    <span className="match-cell-name">
      {name}{" "}
      <span className="player-record" title={playerRecordTitle(record)}>
        {formatPlayerRecord(record)}
      </span>
    </span>
  );
}

export function TorneioRodadaPage() {
  const { id, n } = useParams<{ id: string; n: string }>();
  const eventId = Number(id);
  const roundNum = Number(n);
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [scores, setScores] = useState<Record<number, ScoreDraft>>({});
  const [savedMatchId, setSavedMatchId] = useState<number | null>(null);
  const [woModalOpen, setWoModalOpen] = useState(false);
  const [completarModalOpen, setCompletarModalOpen] = useState(false);
  const [highlightIncomplete, setHighlightIncomplete] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const { data: me, isFetched: meFetched } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const isStaff = Boolean(me && (me.role === "admin" || me.role === "staff"));

  const { data: torneio } = useQuery({
    queryKey: ["torneio", eventId],
    queryFn: () => api.getTorneio(eventId),
    enabled: isStaff,
  });

  const { data: rodada, refetch } = useQuery({
    queryKey: ["rodada", eventId, roundNum],
    queryFn: () => api.getRodada(eventId, roundNum),
    enabled: isStaff,
  });

  useEffect(() => {
    if (savedMatchId == null) return;
    const t = window.setTimeout(() => setSavedMatchId(null), 2500);
    return () => window.clearTimeout(t);
  }, [savedMatchId]);

  const saveMatch = useMutation({
    mutationFn: (matchId: number) => {
      const match = rodada?.matches.find((m) => m.id === matchId);
      if (!match) throw new Error("Partida não encontrada.");
      const s = getMatchScores(matchId, match, scores);
      if (s.p1 === "" || s.p2 === "") {
        throw new Error(
          torneio?.format === "swiss"
            ? "Selecione o placar completo (0-0 para empate intencional no Suíço)."
            : "Selecione o placar completo.",
        );
      }
      return api.updateMatch(eventId, matchId, parseInt(s.p1, 10), parseInt(s.p2, 10));
    },
    onSuccess: async (_data, matchId) => {
      setError("");
      setSavedMatchId(matchId);
      setScores((prev) => {
        const next = { ...prev };
        delete next[matchId];
        return next;
      });
      const refreshed = await refetch();
      const matches = refreshed.data?.matches ?? rodada?.matches ?? [];
      const pending = incompleteMatches(matches).filter((m) => m.id !== matchId);
      const nextMatch = pending[0];
      requestAnimationFrame(() => {
        if (!nextMatch) return;
        const el = document.querySelector<HTMLSelectElement>(
          `select[data-match-id="${nextMatch.id}"][data-score-side="p1"]`,
        );
        el?.focus();
      });
    },
    onError: (e) => {
      setSavedMatchId(null);
      setError((e as Error).message);
    },
  });

  const completar = useMutation({
    mutationFn: () => api.completarRodada(eventId),
    onSuccess: () => {
      setCompletarModalOpen(false);
      setHighlightIncomplete(false);
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      window.location.href = `/torneios/${eventId}`;
    },
    onError: (e) => {
      setCompletarModalOpen(false);
      setHighlightIncomplete(true);
      setError((e as Error).message);
    },
  });

  const dropPlayer = useMutation({
    mutationFn: (pid: number) => api.dropJogador(eventId, pid, true),
    onSuccess: () => {
      setWoModalOpen(false);
      setError("");
      refetch();
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
    },
    onError: (e) => setError((e as Error).message),
  });

  const isActive = rodada?.status === "active";

  useEffect(() => {
    if (!isActive) return;
    const onKey = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey) || e.key !== "Enter") return;
      if (completarModalOpen || woModalOpen) return;
      e.preventDefault();
      setCompletarModalOpen(true);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isActive, completarModalOpen, woModalOpen]);

  useEffect(() => {
    if (rodada?.status !== "active") return;
    const first = incompleteMatches(rodada.matches)[0];
    if (!first) return;
    requestAnimationFrame(() => {
      document
        .querySelector<HTMLSelectElement>(
          `select[data-match-id="${first.id}"][data-score-side="p1"]`,
        )
        ?.focus();
    });
  }, [eventId, roundNum, rodada?.status]);

  if (meFetched && !isStaff) {
    return <Navigate to={`/torneios/${eventId}`} replace />;
  }

  if (!rodada || !torneio) return <p>Carregando...</p>;

  const matchBestOf = (m: Match) => m.best_of ?? torneio.best_of;
  const allowDraw = torneio.format === "swiss";
  const roundBoValues = [...new Set(rodada.matches.map(matchBestOf))].sort((a, b) => a - b);
  const boHeaderLabel =
    roundBoValues.length > 1
      ? `Bo por fase (${roundBoValues.map((b) => `Bo${b}`).join(", ")})`
      : `Melhor de ${roundBoValues[0] ?? torneio.best_of}`;
  const activePlayers =
    torneio.players?.filter((p) => !p.dropped_at).map((p) => ({ id: p.id, name: p.name })) ?? [];
  const records = rodada.player_records ?? {};

  const recordFor = (playerId: number | null | undefined): PlayerRecordWld | undefined =>
    playerId != null ? records[playerId] : undefined;

  const updateScore = (match: Match, field: "p1" | "p2", value: string) => {
    const bestOf = matchBestOf(match);
    const current = getMatchScores(match.id, match, scores);
    const next: ScoreDraft = { ...current, [field]: value };

    if (field === "p1" && next.p2 !== "") {
      const validP2 = validScoresForPlayer(bestOf, allowDraw, 2, next.p1 === "" ? undefined : Number(next.p1));
      if (!validP2.includes(Number(next.p2))) next.p2 = "";
    }
    if (field === "p2" && next.p1 !== "") {
      const validP1 = validScoresForPlayer(bestOf, allowDraw, 1, next.p2 === "" ? undefined : Number(next.p2));
      if (!validP1.includes(Number(next.p1))) next.p1 = "";
    }

    setScores({ ...scores, [match.id]: next });
    setError("");
    setSavedMatchId(null);
    setHighlightIncomplete(false);
  };

  const pending = incompleteMatches(rodada.matches);
  const scoredCount = rodada.matches.filter((m) => !isMatchIncomplete(m)).length;
  const totalPlayable = rodada.matches.filter((m) => !m.is_bye).length;
  const canConclude = isActive && pending.length === 0;

  const tryCompleteRound = () => {
    const missing = incompleteMatches(rodada.matches);
    if (missing.length > 0) {
      setCompletarModalOpen(false);
      setHighlightIncomplete(true);
      setError(
        `Salve o placar antes de concluir: ${missing.map(matchSummaryLabel).join("; ")}.`,
      );
      requestAnimationFrame(() => {
        const el = document.querySelector<HTMLSelectElement>(
          `select[data-match-id="${missing[0].id}"][data-score-side="p1"]`,
        );
        el?.focus();
      });
      return;
    }
    completar.mutate();
  };

  return (
    <div className="rodada-page">
      <header className="rodada-header">
        <div className="rodada-header-main">
          <Link to={`/torneios/${eventId}`} className="torneio-back">
            ← {torneio.name}
          </Link>
          <div className="torneio-manage-title-row">
            <h1>Rodada {roundNum}</h1>
            {isActive && activePlayers.length > 0 && (
              <div className="torneio-overflow">
                <button
                  type="button"
                  className="secondary torneio-overflow-btn"
                  aria-expanded={menuOpen}
                  onClick={() => setMenuOpen((v) => !v)}
                >
                  ⋯
                </button>
                {menuOpen && (
                  <div className="torneio-overflow-menu" role="menu">
                    <button
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        setMenuOpen(false);
                        setWoModalOpen(true);
                      }}
                    >
                      Registrar WO…
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
          <p className="torneio-manage-meta">
            {boHeaderLabel} ·{" "}
            <span className="badge">{rodada.status === "active" ? "em andamento" : rodada.status}</span>
            {" · "}
            {scoredCount}/{rodada.matches.length} partidas com placar
            {totalPlayable > 0 && pending.length > 0 ? ` · ${pending.length} pendente(s)` : ""}
          </p>
          <details className="torneio-advanced rodada-help">
            <summary>Ajuda rápida</summary>
            <p className="field-hint">
              W/L/D ao lado do nome = record antes desta rodada. Salve cada placar; o foco vai para a
              próxima partida. {allowDraw ? "0-0 = empate intencional (Suíço). " : ""}
              <kbd>Ctrl</kbd>+<kbd>Enter</kbd> abre concluir rodada.
            </p>
          </details>
        </div>
        {isActive && (
          <div className="torneio-manage-primary">
            <button
              className="primary"
              type="button"
              onClick={() => setCompletarModalOpen(true)}
              disabled={completar.isPending}
              title={
                canConclude
                  ? undefined
                  : `Ainda faltam ${pending.length} placar(es)`
              }
            >
              {completar.isPending ? "Concluindo…" : "Concluir rodada"}
            </button>
            {!canConclude && (
              <p className="field-hint">
                {pending.length} partida(s) sem placar salvo
              </p>
            )}
          </div>
        )}
      </header>

      {error && <p className="error">{error}</p>}
      {highlightIncomplete && pending.length > 0 && (
        <p className="warning" role="status">
          {pending.length} partida(s) sem placar salvo — destacadas abaixo.
        </p>
      )}

      <div className="match-card-list">
        {rodada.matches.map((m, idx) => {
          const bestOf = matchBestOf(m);
          const s = getMatchScores(m.id, m, scores);
          const p1Options = validScoresForPlayer(
            bestOf,
            allowDraw,
            1,
            s.p2 === "" ? undefined : Number(s.p2),
          );
          const p2Options = validScoresForPlayer(
            bestOf,
            allowDraw,
            2,
            s.p1 === "" ? undefined : Number(s.p1),
          );
          const isSaving = saveMatch.isPending && saveMatch.variables === m.id;
          const justSaved = savedMatchId === m.id;
          const incomplete = isMatchIncomplete(m);
          const showIncomplete = highlightIncomplete && incomplete;
          const saved = m.scores_submitted && !incomplete;

          return (
            <article
              key={m.id}
              className={`match-card${showIncomplete ? " match-card-incomplete" : ""}${saved ? " match-card-saved" : ""}`}
            >
              <div className="match-card-top">
                <span className="match-card-num">Mesa {idx + 1}</span>
                {m.had_rematch && (
                  <span className="badge badge-rematch" title="Já se enfrentaram antes">
                    Rematch
                  </span>
                )}
                {m.is_third_place && <span className="badge">3º–4º</span>}
                {saved && <span className="badge badge-ok">salvo</span>}
                {showIncomplete && <span className="badge badge-warn">pendente</span>}
              </div>

              {m.is_bye ? (
                <div className="match-card-bye">
                  <span className="badge">
                    BYE —{" "}
                    <PlayerNameWithRecord name={m.player1_name} record={recordFor(m.player1_id)} />
                  </span>
                </div>
              ) : m.is_walkover ? (
                <div className="match-card-players">
                  <div className="match-card-side">
                    <PlayerNameWithRecord name={m.player1_name} record={recordFor(m.player1_id)} />
                    <span>
                      {m.score_p1} <span className="badge">WO</span>
                    </span>
                  </div>
                  <span className="match-card-vs">×</span>
                  <div className="match-card-side">
                    <PlayerNameWithRecord
                      name={m.player2_name ?? "—"}
                      record={recordFor(m.player2_id)}
                    />
                    <span>{m.score_p2}</span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="match-card-players">
                    <div className="match-card-side">
                      <PlayerNameWithRecord name={m.player1_name} record={recordFor(m.player1_id)} />
                      <MatchBadges match={m} bestOf={bestOf} />
                      <ScoreSelect
                        label={`Games de ${m.player1_name}`}
                        value={s.p1}
                        options={p1Options}
                        bestOf={bestOf}
                        allowDraw={allowDraw}
                        onChange={(v) => updateScore(m, "p1", v)}
                        disabled={!isActive}
                        matchId={m.id}
                        side="p1"
                      />
                    </div>
                    <span className="match-card-vs">×</span>
                    <div className="match-card-side">
                      <PlayerNameWithRecord
                        name={m.player2_name ?? "—"}
                        record={recordFor(m.player2_id)}
                      />
                      <MatchBadges match={m} bestOf={bestOf} />
                      <ScoreSelect
                        label={`Games de ${m.player2_name ?? "jogador 2"}`}
                        value={s.p2}
                        options={p2Options}
                        bestOf={bestOf}
                        allowDraw={allowDraw}
                        onChange={(v) => updateScore(m, "p2", v)}
                        disabled={!isActive}
                        matchId={m.id}
                        side="p2"
                      />
                    </div>
                  </div>
                  {isActive && (
                    <div className="match-card-actions">
                      <button
                        className="secondary"
                        type="button"
                        onClick={() => saveMatch.mutate(m.id)}
                        disabled={isSaving}
                      >
                        {isSaving ? "Salvando…" : "Salvar placar"}
                      </button>
                      {justSaved && (
                        <span className="save-feedback success" role="status">
                          Salvo
                        </span>
                      )}
                    </div>
                  )}
                </>
              )}
            </article>
          );
        })}
      </div>

      <PlayerPickerModal
        open={woModalOpen}
        title="Walkover (WO)"
        description="O oponente recebe vitória automática. Esta ação não pode ser desfeita — confirme o jogador que desistiu da partida."
        players={activePlayers}
        confirmLabel="Confirmar WO"
        pending={dropPlayer.isPending}
        onClose={() => setWoModalOpen(false)}
        onConfirm={(pid) => dropPlayer.mutate(pid)}
      />

      <ConfirmModal
        open={completarModalOpen}
        title="Concluir rodada"
        message="Todos os placares foram informados? Após concluir, só será possível alterar resultados reabrindo a rodada."
        confirmLabel="Concluir"
        pending={completar.isPending}
        onClose={() => setCompletarModalOpen(false)}
        onConfirm={tryCompleteRound}
      />
    </div>
  );
}
