import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { Torneio } from "../api/types";

type Props = {
  eventId: number;
  torneio: Torneio;
};

export function TorneioDraftEditPanel({ eventId, torneio }: Props) {
  const qc = useQueryClient();
  const { data: tcgGames } = useQuery({
    queryKey: ["tcg-games"],
    queryFn: () => api.listTcgGames(),
  });

  const [name, setName] = useState(torneio.name);
  const [eventDate, setEventDate] = useState(torneio.event_date);
  const [startTime, setStartTime] = useState(torneio.start_time ?? "");
  const [description, setDescription] = useState(torneio.description ?? "");
  const [tcgGameId, setTcgGameId] = useState(torneio.tcg_game?.id?.toString() ?? "");
  const [entryFee, setEntryFee] = useState(String(torneio.entry_fee ?? 0));
  const [bestOf, setBestOf] = useState(torneio.best_of ?? 3);
  const [maxRounds, setMaxRounds] = useState(
    torneio.max_rounds != null ? String(torneio.max_rounds) : "",
  );
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setName(torneio.name);
    setEventDate(torneio.event_date);
    setStartTime(torneio.start_time ?? "");
    setDescription(torneio.description ?? "");
    setTcgGameId(torneio.tcg_game?.id?.toString() ?? "");
    setEntryFee(String(torneio.entry_fee ?? 0));
    setBestOf(torneio.best_of ?? 3);
    setMaxRounds(torneio.max_rounds != null ? String(torneio.max_rounds) : "");
  }, [
    torneio.id,
    torneio.name,
    torneio.event_date,
    torneio.start_time,
    torneio.description,
    torneio.tcg_game?.id,
    torneio.entry_fee,
    torneio.best_of,
    torneio.max_rounds,
  ]);

  const isDirty = useMemo(() => {
    const rounds = maxRounds ? parseInt(maxRounds, 10) : null;
    return (
      name.trim() !== torneio.name ||
      eventDate !== torneio.event_date ||
      (startTime || null) !== (torneio.start_time || null) ||
      (description.trim() || null) !== (torneio.description?.trim() || null) ||
      (tcgGameId ? Number(tcgGameId) : null) !== (torneio.tcg_game?.id ?? null) ||
      (parseFloat(entryFee) || 0) !== (torneio.entry_fee ?? 0) ||
      bestOf !== (torneio.best_of ?? 3) ||
      rounds !== (torneio.max_rounds ?? null)
    );
  }, [name, eventDate, startTime, description, tcgGameId, entryFee, bestOf, maxRounds, torneio]);

  const save = useMutation({
    mutationFn: () => {
      if (!name.trim()) throw new Error("Nome do torneio é obrigatório.");
      if (!tcgGameId) throw new Error("Selecione o TCG do torneio.");
      const rounds = maxRounds.trim() ? parseInt(maxRounds, 10) : null;
      return api.updateTorneio(eventId, {
        name: name.trim(),
        event_date: eventDate,
        start_time: startTime.trim() || null,
        description: description.trim() || null,
        tcg_game_id: Number(tcgGameId),
        entry_fee: parseFloat(entryFee) || 0,
        best_of: bestOf,
        max_rounds: torneio.format === "swiss" ? rounds : undefined,
      });
    },
    onSuccess: async () => {
      setError("");
      await qc.invalidateQueries({ queryKey: ["torneio", eventId] });
      await qc.invalidateQueries({ queryKey: ["torneios"] });
      await qc.invalidateQueries({ queryKey: ["calendar"] });
    },
    onError: (e) => setError((e as Error).message),
  });

  return (
    <section className="torneio-panel torneio-edit-panel">
      <div className="torneio-panel-head">
        <button
          type="button"
          className="torneio-edit-toggle"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <h2>Editar torneio</h2>
          <span aria-hidden>{open ? "▾" : "▸"}</span>
        </button>
        <p className="field-hint">Formato e premiação não podem ser alterados após a criação.</p>
      </div>
      {open && (
        <div className="admin-form-grid torneio-edit-form">
          <div className="form-row">
            <label htmlFor="edit-torneio-name">Nome</label>
            <input
              id="edit-torneio-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="form-row">
            <label htmlFor="edit-torneio-tcg">TCG</label>
            <select
              id="edit-torneio-tcg"
              value={tcgGameId}
              onChange={(e) => setTcgGameId(e.target.value)}
            >
              <option value="">— selecionar —</option>
              {tcgGames?.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-row">
            <label htmlFor="edit-torneio-date">Data</label>
            <input
              id="edit-torneio-date"
              type="date"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
            />
          </div>
          <div className="form-row">
            <label htmlFor="edit-torneio-time">Horário (opcional)</label>
            <input
              id="edit-torneio-time"
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
            />
          </div>
          <div className="form-row torneio-edit-field-full">
            <label htmlFor="edit-torneio-desc">Descrição (calendário)</label>
            <textarea
              id="edit-torneio-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Breve texto para o calendário público"
            />
          </div>
          {torneio.format === "swiss" && (
            <div className="form-row">
              <label htmlFor="edit-torneio-rounds">Rodadas máximas (vazio = automático)</label>
              <input
                id="edit-torneio-rounds"
                type="number"
                min={1}
                value={maxRounds}
                onChange={(e) => setMaxRounds(e.target.value)}
              />
            </div>
          )}
          <div className="form-row">
            <label htmlFor="edit-torneio-fee">Valor inscrição (R$)</label>
            <input
              id="edit-torneio-fee"
              type="number"
              step="0.01"
              value={entryFee}
              onChange={(e) => setEntryFee(e.target.value)}
            />
          </div>
          <div className="form-row">
            <label htmlFor="edit-torneio-bo">Melhor de (padrão global)</label>
            <select
              id="edit-torneio-bo"
              value={bestOf}
              onChange={(e) => setBestOf(+e.target.value)}
            >
              <option value={1}>1</option>
              <option value={3}>3</option>
              <option value={5}>5</option>
            </select>
          </div>
          {error && (
            <p className="error torneio-edit-field-full" role="alert">
              {error}
            </p>
          )}
          <div className="torneio-edit-actions torneio-edit-field-full">
            <button
              type="button"
              className="primary"
              disabled={!isDirty || !name.trim() || save.isPending}
              onClick={() => save.mutate()}
            >
              {save.isPending ? "Salvando…" : "Salvar alterações"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
