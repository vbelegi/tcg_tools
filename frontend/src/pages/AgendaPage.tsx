import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

type Announcement = {
  id: number;
  title: string;
  event_date: string;
  description: string | null;
  start_time: string | null;
  location: string | null;
};

export function AgendaPage() {
  const qc = useQueryClient();
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [title, setTitle] = useState("");
  const [eventDate, setEventDate] = useState(today.toISOString().slice(0, 10));
  const [startTime, setStartTime] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [editing, setEditing] = useState<Announcement | null>(null);
  const [error, setError] = useState("");

  const { data = [], isLoading } = useQuery({
    queryKey: ["calendar-announcements", year, month],
    queryFn: () => api.listCalendarAnnouncements(year, month),
  });

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
  };

  return (
    <div className="admin-page">
      <header className="torneio-manage-header">
        <div>
          <h1>Agenda</h1>
          <p className="torneio-manage-meta">
            Eventos no calendário (sem inscrição) · {data.length} no mês
          </p>
        </div>
      </header>

      {error && <p className="error">{error}</p>}

      <details className="torneio-advanced admin-create-panel" open>
        <summary>{editing ? "Editar evento" : "Novo evento"}</summary>
        <form onSubmit={onSubmit} className="admin-form-dense">
          <div className="admin-form-grid">
            <div className="form-row">
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
            <div className="form-row">
              <label htmlFor="agenda-location">Local</label>
              <input
                id="agenda-location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
            <div className="form-row">
              <label htmlFor="agenda-desc">Descrição</label>
              <textarea
                id="agenda-desc"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>
          <button
            className="primary"
            type="submit"
            disabled={create.isPending || update.isPending}
          >
            {editing ? (update.isPending ? "Salvando…" : "Salvar") : create.isPending ? "Criando…" : "Criar"}
          </button>
          {editing && (
            <button className="secondary" type="button" onClick={resetForm}>
              Cancelar
            </button>
          )}
        </form>
      </details>

      <section className="resultado-section">
        <div className="admin-inline-add">
          <div className="form-row admin-inline-add-field">
            <label htmlFor="agenda-month">Mês</label>
            <input
              id="agenda-month"
              type="month"
              value={`${year}-${String(month).padStart(2, "0")}`}
              onChange={(e) => {
                const [y, m] = e.target.value.split("-").map(Number);
                setYear(y);
                setMonth(m);
              }}
            />
          </div>
        </div>

        {isLoading && <p>Carregando...</p>}

        <div className="resultado-table-wrap">
          <table className="resultado-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Título</th>
                <th>Horário</th>
                <th>Local</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.id}>
                  <td>{row.event_date}</td>
                  <td>{row.title}</td>
                  <td>{row.start_time ?? "—"}</td>
                  <td>{row.location ?? "—"}</td>
                  <td className="admin-row-actions">
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
