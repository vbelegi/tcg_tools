import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ConfirmModal } from "../../components/ConfirmModal";
import { PlayerPickerModal } from "../../components/PlayerPickerModal";
import { api } from "../../api/client";
import type { Match } from "../../api/types";
import { formatPlayerRecord, playerRecordTitle, type PlayerRecordWld } from "../../utils/playerRecord";
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
}: {
  value: string;
  options: number[];
  bestOf: number;
  allowDraw: boolean;
  onChange: (v: string) => void;
  disabled?: boolean;
  label: string;
}) {
  const numericValue = value === "" ? null : Number(value);
  const optionSet = new Set(options);
  if (numericValue !== null && !Number.isNaN(numericValue) && !optionSet.has(numericValue)) {
    optionSet.add(numericValue);
  }
  const sorted = Array.from(optionSet).sort((a, b) => a - b);

  return (
    <select
      className="score-select"
      aria-label={label}
      title={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
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

  const { data: torneio } = useQuery({
    queryKey: ["torneio", eventId],
    queryFn: () => api.getTorneio(eventId),
  });

  const { data: rodada, refetch } = useQuery({
    queryKey: ["rodada", eventId, roundNum],
    queryFn: () => api.getRodada(eventId, roundNum),
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
        throw new Error("Selecione o placar completo (0-0 para empate intencional no Suíço).");
      }
      return api.updateMatch(eventId, matchId, parseInt(s.p1, 10), parseInt(s.p2, 10));
    },
    onSuccess: (_data, matchId) => {
      setError("");
      setSavedMatchId(matchId);
      setScores((prev) => {
        const next = { ...prev };
        delete next[matchId];
        return next;
      });
      refetch();
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
      qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      window.location.href = `/torneios/${eventId}`;
    },
    onError: (e) => setError((e as Error).message),
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

  if (!rodada || !torneio) return <p>Carregando...</p>;

  const isActive = rodada.status === "active";
  const bestOf = torneio.best_of;
  const allowDraw = torneio.format === "swiss";
  const activePlayers =
    torneio.players?.filter((p) => !p.dropped_at).map((p) => ({ id: p.id, name: p.name })) ?? [];
  const records = rodada.player_records ?? {};

  const recordFor = (playerId: number | null | undefined): PlayerRecordWld | undefined =>
    playerId != null ? records[playerId] : undefined;

  const updateScore = (match: Match, field: "p1" | "p2", value: string) => {
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
  };

  return (
    <div>
      <Link to={`/torneios/${eventId}`}>← Voltar</Link>
      <h1>Rodada {roundNum}</h1>
      <p>
        Melhor de {bestOf} · Status: {rodada.status}
      </p>
      <p style={{ fontSize: "0.9rem", opacity: 0.85 }}>
        Placar ao lado de cada jogador. Ao lado do nome: <strong>W/L/D</strong> (vitórias / derrotas /
        empates) antes desta rodada. 1 = vitória por tempo (Bo3/Bo5). 0-0 = empate (Suíço). — = não
        informado.
      </p>
      {error && <p className="error">{error}</p>}

      <table style={{ marginTop: "1rem" }}>
        <thead>
          <tr>
            <th>Jogador 1</th>
            <th aria-hidden="true" />
            <th>Jogador 2</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {rodada.matches.map((m) => {
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

            return (
              <tr key={m.id}>
                <td>
                  {m.is_bye ? (
                    <span className="badge">
                      BYE —{" "}
                      <PlayerNameWithRecord name={m.player1_name} record={recordFor(m.player1_id)} />
                    </span>
                  ) : m.is_walkover ? (
                    <div className="match-cell">
                      <PlayerNameWithRecord name={m.player1_name} record={recordFor(m.player1_id)} />
                      <span>
                        {m.score_p1} <span className="badge">WO</span>
                      </span>
                    </div>
                  ) : (
                    <div className="match-cell">
                      <PlayerNameWithRecord name={m.player1_name} record={recordFor(m.player1_id)} />
                      <ScoreSelect
                        label={`Games de ${m.player1_name}`}
                        value={s.p1}
                        options={p1Options}
                        bestOf={bestOf}
                        allowDraw={allowDraw}
                        onChange={(v) => updateScore(m, "p1", v)}
                        disabled={!isActive}
                      />
                    </div>
                  )}
                </td>
                <td className="match-vs">
                  {!m.is_bye && !m.is_walkover && "×"}
                </td>
                <td>
                  {m.is_bye ? (
                    "—"
                  ) : m.is_walkover ? (
                    <div className="match-cell">
                      <PlayerNameWithRecord
                        name={m.player2_name ?? "—"}
                        record={recordFor(m.player2_id)}
                      />
                      <span>{m.score_p2}</span>
                    </div>
                  ) : (
                    <div className="match-cell">
                      <PlayerNameWithRecord
                        name={m.player2_name ?? "—"}
                        record={recordFor(m.player2_id)}
                      />
                      <ScoreSelect
                        label={`Games de ${m.player2_name ?? "jogador 2"}`}
                        value={s.p2}
                        options={p2Options}
                        bestOf={bestOf}
                        allowDraw={allowDraw}
                        onChange={(v) => updateScore(m, "p2", v)}
                        disabled={!isActive}
                      />
                    </div>
                  )}
                  {m.had_rematch && (
                    <span className="badge badge-rematch" title="Estes jogadores já se enfrentaram antes">
                      Rematch
                    </span>
                  )}
                </td>
                <td>
                  {!m.is_bye && !m.is_walkover && isActive && (
                    <>
                      <button
                        className="secondary"
                        onClick={() => saveMatch.mutate(m.id)}
                        disabled={isSaving}
                      >
                        {isSaving ? "Salvando…" : "Salvar"}
                      </button>
                      {justSaved && (
                        <div className="save-feedback success" role="status">
                          Salvo com sucesso
                        </div>
                      )}
                    </>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {isActive && (
        <div style={{ marginTop: "1.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            className="primary"
            onClick={() => setCompletarModalOpen(true)}
            disabled={completar.isPending}
          >
            Concluir rodada
          </button>
          {activePlayers.length > 0 && (
            <button className="secondary" onClick={() => setWoModalOpen(true)}>
              Registrar WO…
            </button>
          )}
        </div>
      )}

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
        onConfirm={() => completar.mutate()}
      />
    </div>
  );
}
