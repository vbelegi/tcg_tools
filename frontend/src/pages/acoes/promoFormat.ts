export type PromoPhase = "scheduled" | "running" | "ended";

/** Local calendar day as YYYY-MM-DD, so ISO date strings compare safely. */
export function todayIso(now: Date = new Date()): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatDate(iso: string): string {
  return iso.split("-").reverse().join("/");
}

export function formatCountdown(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
}

export function formatDateTime(iso: string): string {
  const [datePart, timePart] = iso.replace("Z", "").split("T");
  if (!datePart) return iso;
  const hhmm = (timePart || "").slice(0, 5);
  return hhmm ? `${formatDate(datePart)} ${hhmm}` : formatDate(datePart);
}

export function formatPeriod(startDate: string, endDate: string): string {
  return `${formatDate(startDate)} a ${formatDate(endDate)}`;
}

export function promoPhase(
  action: { start_date: string; end_date: string },
  today: string = todayIso(),
): PromoPhase {
  if (action.end_date < today) return "ended";
  if (action.start_date > today) return "scheduled";
  return "running";
}

export function phaseLabel(phase: PromoPhase): string {
  if (phase === "ended") return "encerrada";
  if (phase === "scheduled") return "em breve";
  return "em andamento";
}
