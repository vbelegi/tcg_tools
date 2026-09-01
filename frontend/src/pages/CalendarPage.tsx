import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import type { Torneio } from "../api/types";

const WEEKDAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

const MONTHS = [
  "janeiro",
  "fevereiro",
  "março",
  "abril",
  "maio",
  "junho",
  "julho",
  "agosto",
  "setembro",
  "outubro",
  "novembro",
  "dezembro",
];

type CalendarAnnouncement = {
  id: number;
  title: string;
  event_date: string;
  description: string | null;
  start_time: string | null;
  location: string | null;
};

type DayItem =
  | { kind: "tournament"; data: Torneio }
  | { kind: "announcement"; data: CalendarAnnouncement };

function statusLabel(status: Torneio["status"], registrationOpen?: boolean): string {
  if (status === "draft") return registrationOpen ? "Inscrições abertas" : "Inscrições fechadas";
  if (status === "running") return "Em andamento";
  return "Concluído";
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function CalendarPage() {
  const today = new Date();
  const [cursor, setCursor] = useState({
    year: today.getFullYear(),
    month: today.getMonth() + 1,
  });
  const [selectedDay, setSelectedDay] = useState<number | null>(today.getDate());

  const { data: me } = useQuery({
    queryKey: ["auth-me"],
    queryFn: () => api.authMe(),
    retry: false,
  });
  const isStaff = Boolean(me && (me.role === "admin" || me.role === "staff"));

  const { data, isLoading } = useQuery({
    queryKey: ["calendar", cursor.year, cursor.month],
    queryFn: () => api.getCalendar(cursor.year, cursor.month),
  });
  const tournaments = data?.tournaments ?? [];
  const announcements = data?.announcements ?? [];

  const byDay = useMemo(() => {
    const map = new Map<number, DayItem[]>();
    const add = (day: number, item: DayItem) => {
      const list = map.get(day) ?? [];
      list.push(item);
      map.set(day, list);
    };
    for (const ev of tournaments) {
      add(Number(ev.event_date.slice(8, 10)), { kind: "tournament", data: ev });
    }
    for (const ann of announcements) {
      add(Number(ann.event_date.slice(8, 10)), { kind: "announcement", data: ann });
    }
    return map;
  }, [tournaments, announcements]);

  const firstWeekday = new Date(cursor.year, cursor.month - 1, 1).getDay();
  const daysInMonth = new Date(cursor.year, cursor.month, 0).getDate();
  const cells: Array<number | null> = [
    ...Array.from({ length: firstWeekday }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];
  while (cells.length % 7 !== 0) cells.push(null);

  const selectedItems = selectedDay != null ? (byDay.get(selectedDay) ?? []) : [];

  const shiftMonth = (delta: number) => {
    const d = new Date(cursor.year, cursor.month - 1 + delta, 1);
    const next = { year: d.getFullYear(), month: d.getMonth() + 1 };
    setCursor(next);
    const isCurrentMonth =
      next.year === today.getFullYear() && next.month === today.getMonth() + 1;
    setSelectedDay(isCurrentMonth ? today.getDate() : null);
  };

  const ctaFor = (t: Torneio): { label: string; to: string } | null => {
    const enrolled = Boolean(me && (t.participant_user_ids ?? []).includes(me.id));
    if (t.status === "finished") {
      return { label: "Ver resultado", to: `/torneios/${t.id}/resultado` };
    }
    if (t.status === "draft" && t.registration_open) {
      if (!me) {
        return {
          label: "Entrar para se inscrever",
          to: `/?auth=login&next=${encodeURIComponent(`/torneios/${t.id}`)}`,
        };
      }
      return {
        label: enrolled ? "Ver torneio" : "Inscrever-me",
        to: `/torneios/${t.id}`,
      };
    }
    if (t.status === "running" && (isStaff || enrolled)) {
      return { label: "Ver pairings / classificação", to: `/torneios/${t.id}` };
    }
    return null;
  };

  return (
    <div className="calendar-page">
      <h1>Calendário</h1>
      <div className="calendar-layout">
        <section className="calendar-grid-wrap">
          <div className="calendar-header">
            <h2>
              {capitalize(MONTHS[cursor.month - 1])} {cursor.year}
            </h2>
            <div className="calendar-nav">
              <button
                type="button"
                className="secondary"
                onClick={() => shiftMonth(-1)}
                aria-label="Mês anterior"
              >
                ‹
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => shiftMonth(1)}
                aria-label="Próximo mês"
              >
                ›
              </button>
            </div>
          </div>
          <div className="calendar-weekdays">
            {WEEKDAYS.map((d) => (
              <div key={d}>{d}</div>
            ))}
          </div>
          <div className="calendar-grid">
            {cells.map((day, idx) => {
              const dayItems = day != null ? (byDay.get(day) ?? []) : [];
              const selected = day != null && day === selectedDay;
              return (
                <button
                  key={idx}
                  type="button"
                  className={`calendar-day${day == null ? " empty" : ""}${selected ? " selected" : ""}`}
                  disabled={day == null}
                  onClick={() => day != null && setSelectedDay(day)}
                >
                  {day != null && <span className="calendar-day-num">{day}</span>}
                  <div className="calendar-chips">
                    {dayItems.slice(0, 2).map((item) =>
                      item.kind === "tournament" ? (
                        <span
                          key={`t-${item.data.id}`}
                          className="calendar-chip"
                          style={{
                            color: item.data.tcg_game?.color_hex ?? "var(--primary)",
                            borderColor: item.data.tcg_game?.color_hex ?? "var(--border)",
                          }}
                          title={item.data.name}
                        >
                          {item.data.name}
                        </span>
                      ) : (
                        <span
                          key={`a-${item.data.id}`}
                          className="calendar-chip calendar-chip-announcement"
                          title={item.data.title}
                        >
                          {item.data.title}
                        </span>
                      ),
                    )}
                    {dayItems.length > 2 && (
                      <span className="calendar-chip-more">+{dayItems.length - 2}</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
          {isLoading && <p>Carregando…</p>}
        </section>

        <aside className="calendar-detail">
          <h2>
            {selectedDay != null
              ? `${selectedDay} de ${MONTHS[cursor.month - 1]}`
              : "Selecione um dia"}
          </h2>
          {selectedDay == null && (
            <p className="calendar-empty">Clique em um dia para ver os eventos.</p>
          )}
          {selectedDay != null && selectedItems.length === 0 && (
            <div className="calendar-empty">
              <p>Nenhum evento neste dia.</p>
            </div>
          )}
          {selectedItems.map((item) => {
            if (item.kind === "announcement") {
              const ann = item.data;
              return (
                <article key={`a-${ann.id}`} className="calendar-event-card calendar-announcement-card">
                  <div className="calendar-event-top">
                    <h3>{ann.title}</h3>
                    <span className="badge badge-announcement">Evento</span>
                  </div>
                  {ann.description && <p className="calendar-event-desc">{ann.description}</p>}
                  <ul className="calendar-event-meta">
                    {ann.start_time && <li>Horário: {ann.start_time}</li>}
                    {ann.location && <li>Local: {ann.location}</li>}
                  </ul>
                </article>
              );
            }

            const t = item.data;
            const cta = ctaFor(t);
            return (
              <article key={`t-${t.id}`} className="calendar-event-card">
                {t.tcg_game && (
                  <p className="calendar-event-tcg" style={{ color: t.tcg_game.color_hex }}>
                    {t.tcg_game.name}
                  </p>
                )}
                <div className="calendar-event-top">
                  <h3>{t.name}</h3>
                  <span className="badge">{statusLabel(t.status, t.registration_open)}</span>
                </div>
                {t.description && <p className="calendar-event-desc">{t.description}</p>}
                <ul className="calendar-event-meta">
                  {t.start_time && <li>Horário: {t.start_time}</li>}
                  <li>Formato: {t.format === "swiss" ? "Suíço" : "Eliminatória"}</li>
                  <li>Inscrição: R$ {t.entry_fee.toFixed(2)}</li>
                  <li>Inscritos: {t.player_count}</li>
                </ul>
                {cta && (
                  <Link
                    className="primary"
                    to={cta.to}
                    style={{ display: "inline-block", marginTop: "0.75rem" }}
                  >
                    {cta.label}
                  </Link>
                )}
                {!cta && t.status === "draft" && !t.registration_open && (
                  <p className="calendar-event-note">Inscrições fechadas.</p>
                )}
                {!cta && t.status === "running" && (
                  <p className="calendar-event-note">
                    Em andamento — pairings só para inscritos logados.
                  </p>
                )}
              </article>
            );
          })}
        </aside>
      </div>
    </div>
  );
}
