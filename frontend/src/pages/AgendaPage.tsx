import { FormEvent, useCallback, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import { ListFilterBar } from "../components/ListFilterBar";

type Announcement = {
  id: number;
  title: string;
  event_date: string;
  description: string | null;
  start_time: string | null;
  location: string | null;
};

function monthBounds(year: number, month: number): { from: string; to: string } {
  const last = new Date(year, month, 0).getDate();
  const mm = String(month).padStart(2, "0");
  return {
    from: `${year}-${mm}-01`,
    to: `${year}-${mm}-${String(last).padStart(2, "0")}`,
  };
}

export function AgendaPage() {
  const qc = useQueryClient();
  const today = useMemo(() => new Date(), []);
  const defaultBounds = useMemo(
    () => monthBounds(today.getFullYear(), today.getMonth() + 1),
    [today],
  );

  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const dateFrom = params.get("from") ?? defaultBounds.from;
  const dateTo = params.get("to") ?? defaultBounds.to;

  const [title, setTitle] = useState("");
  const [eventDate, setEventDate] = useState(today.toISOString().slice(0, 10));
  const [startTime, setStartTime] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [editing, setEditing] = useState<Announcement | null>(null);
  const [error, setError] = useState("");

  const { data = [], isLoading } = useQuery({
    queryKey: ["calendar-announcements", q, dateFrom, dateTo],
    queryFn: () =>
      api.listCalendarAnnouncements({
        q: q || undefined,
        from: dateFrom || undefined,
        to: dateTo || undefined,
      }),
  });

  const updateFilters = useCallback(
    (changes: { q?: string; from?: string; to?: string }) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (changes.q !== undefined) {
            if (changes.q) next.set("q", changes.q);
            else next.delete("q");
          }
          if (changes.from !== undefined) {
            if (changes.from) next.set("from", changes.from);
            else next.delete("from");
          }
          if (changes.to !== undefined) {
            if (changes.to) next.set("to", changes.to);
            else next.delete("to");
          }
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  const onSearchChange = useCallback(
    (value: string) => updateFilters({ q: value }),
    [updateFilters],
  );

  const resetForm = () => {
    setTitle("");
    setEventDate(today.toISOString().slice(0, 10));
    setStartTime("");
    setLocation("");
    setDescription("");
    setEditing(null);
    setError("");
  };

  const invalidate = async () => {
    await qc.invalidateQueries({ queryKey: ["calendar-announcements"] });
    await qc.invalidateQueries({ queryKey: ["calendar"] });
  };

  const create = useMutation({
    mutationFn: () =>
      api.createCalendarAnnouncement({
        title: title.trim(),
        event_date: eventDate,
        description: description.trim() || null,
        start_time: startTime.trim() || null,
        location: location.trim() || null,
      }),
    onSuccess: async () => {
      resetForm();
      await invalidate();
    },
    onError: (e) => setError((e as Error).message),
  });

  const update = useMutation({
    mutationFn: () =>
      api.updateCalendarAnnouncement(editing!.id, {
        title: title.trim(),
        event_date: eventDate,
        description: description.trim() || null,
        start_time: startTime.trim() || null,
        location: location.trim() || null,
      }),
    onSuccess: async () => {
      resetForm();
      await invalidate();
    },
    onError: (e) => setError((e as Error).message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.deleteCalendarAnnouncement(id),
    onSuccess: async () => {
      if (editing?.id) resetForm();
      await invalidate();
    },
    onError: (e) => setError((e as Error).message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Título é obrigatório.");
      return;
    }
    if (editing) update.mutate();
    else create.mutate();
  };

  const startEdit = (row: Announcement) => {
    setEditing(row);
    setTitle(row.title);
    setEventDate(row.event_date);
    setStartTime(row.start_time ?? "");
    setLocation(row.location ?? "");
    setDescription(row.description ?? "");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const hasFilters = Boolean(q) || dateFrom !== defaultBounds.from || dateTo !== defaultBounds.to;

  return (
    <div className="admin-page agenda-page">
      <header className="torneio-manage-header">
        <div>
          <h1>Agenda</h1>
          <p className="torneio-manage-meta">
            Eventos no calendário (sem inscrição) · {data.length} no período
          </p>
        </div>
      </header>

      {error && <p className="error">{error}</p>}

      <details className="torneio-advanced admin-create-panel" open>
        <summary>{editing ? "Editar evento" : "Novo evento"}</summary>
        <form onSubmit={onSubmit} className="admin-form-dense">
          <div className="admin-form-grid agenda-form-grid">
            <div className="form-row agenda-field-full">
              <label htmlFor="agenda-title">Título</label>
              <input
                id="agenda-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            <div className="form-row">
              <label htmlFor="agenda-date">Data</label>
              <input
                id="agenda-date"
                type="date"
                value={eventDate}
                onChange={(e) => setEventDate(e.target.value)}
                required
              />
            </div>
            <div className="form-row">
              <label htmlFor="agenda-time">Horário</label>
              <input
                id="agenda-time"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </div>
            <div className="form-row agenda-field-full">
              <label htmlFor="agenda-location">Local</label>
              <input
                id="agenda-location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
            <div className="form-row agenda-field-full">
              <label htmlFor="agenda-desc">Descrição</label>
              <textarea
                id="agenda-desc"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>
          <div className="agenda-form-actions">
            <button
              className="primary"
              type="submit"
              disabled={create.isPending || update.isPending}
            >
              {editing
                ? update.isPending
                  ? "Salvando…"
                  : "Salvar"
                : create.isPending
                  ? "Criando…"
                  : "Criar"}
            </button>
            {editing && (
              <button className="secondary" type="button" onClick={resetForm}>
                Cancelar
              </button>
            )}
          </div>
        </form>
      </details>

      <section className="resultado-section">
        <ListFilterBar
          searchId="agenda-filter-q"
          searchLabel="Buscar por título"
          searchPlaceholder="Ex.: pré-release"
          searchValue={q}
          onSearchChange={onSearchChange}
          dateFrom={dateFrom}
          dateTo={dateTo}
          onDateFromChange={(value) => updateFilters({ from: value })}
          onDateToChange={(value) => updateFilters({ to: value })}
          resultCount={data.length}
        />

        {isLoading && <p>Carregando...</p>}

        {!isLoading && data.length === 0 && (
          <p className="muted">
            {hasFilters ? "Nenhum evento encontrado com esses filtros." : "Nenhum evento neste período."}
          </p>
        )}

        <ul className="agenda-card-list">
          {data.map((row) => (
            <li
              key={row.id}
              className={editing?.id === row.id ? "agenda-card agenda-card-editing" : "agenda-card"}
            >
              <div className="agenda-card-top">
                <strong>{row.title}</strong>
                <span className="badge">{row.event_date}</span>
              </div>
              <ul className="agenda-card-meta">
                <li>Horário: {row.start_time ?? "—"}</li>
                <li>Local: {row.location ?? "—"}</li>
              </ul>
              {row.description && <p className="agenda-card-desc">{row.description}</p>}
              <div className="admin-row-actions agenda-card-actions">
                <button className="secondary" type="button" onClick={() => startEdit(row)}>
                  Editar
                </button>
                <button
                  className="secondary danger"
                  type="button"
                  onClick={() => {
                    if (window.confirm(`Excluir "${row.title}"?`)) remove.mutate(row.id);
                  }}
                  disabled={remove.isPending}
                >
                  Excluir
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
