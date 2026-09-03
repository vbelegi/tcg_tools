export type CalendarPromoAction = {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  description: string | null;
  type_label: string;
};

export type PromoBandCell = {
  promo: CalendarPromoAction;
  day: number;
  openLeft: boolean;
  openRight: boolean;
  isStart: boolean;
  isEnd: boolean;
  extendLeft: boolean;
  extendRight: boolean;
  showLabel: boolean;
  lane: number;
};

function parseIsoDate(iso: string): Date {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

export function clipPromoToMonth(
  promo: Pick<CalendarPromoAction, "start_date" | "end_date">,
  year: number,
  month: number,
): { startDay: number; endDay: number } | null {
  const monthStart = new Date(year, month - 1, 1);
  const monthEnd = new Date(year, month, 0);
  const start = parseIsoDate(promo.start_date);
  const end = parseIsoDate(promo.end_date);
  const clipStart = start > monthStart ? start : monthStart;
  const clipEnd = end < monthEnd ? end : monthEnd;
  if (clipStart > clipEnd) return null;
  return { startDay: clipStart.getDate(), endDay: clipEnd.getDate() };
}

export function promoBandForDay(
  promo: CalendarPromoAction,
  year: number,
  month: number,
  day: number,
): PromoBandCell | null {
  const clip = clipPromoToMonth(promo, year, month);
  if (!clip || day < clip.startDay || day > clip.endDay) return null;

  const weekday = new Date(year, month - 1, day).getDay();
  const monthStart = new Date(year, month - 1, 1);
  const monthEnd = new Date(year, month, 0);
  const start = parseIsoDate(promo.start_date);
  const end = parseIsoDate(promo.end_date);
  const isStart = day === clip.startDay;
  const isEnd = day === clip.endDay;
  const prevInRange = day > 1 && day - 1 >= clip.startDay;
  const nextInRange = day < monthEnd.getDate() && day + 1 <= clip.endDay;
  const openLeft = (isStart && start < monthStart) || (weekday === 0 && prevInRange);
  const openRight = (isEnd && end > monthEnd) || (weekday === 6 && nextInRange);

  return {
    promo,
    day,
    openLeft,
    openRight,
    isStart,
    isEnd,
    extendLeft: !isStart && weekday !== 0,
    extendRight: !isEnd && weekday !== 6,
    showLabel: isStart,
    lane: 0,
  };
}

export function assignPromoLanes(
  promos: CalendarPromoAction[],
  year: number,
  month: number,
): Map<number, number> {
  const clipped = promos
    .map((promo) => {
      const clip = clipPromoToMonth(promo, year, month);
      return clip ? { promo, clip } : null;
    })
    .filter((row): row is { promo: CalendarPromoAction; clip: { startDay: number; endDay: number } } => row != null)
    .sort((a, b) => a.clip.startDay - b.clip.startDay || a.promo.id - b.promo.id);

  const laneEnds: number[] = [];
  const lanes = new Map<number, number>();
  for (const { promo, clip } of clipped) {
    let lane = laneEnds.findIndex((end) => end < clip.startDay);
    if (lane === -1) {
      lane = laneEnds.length;
      laneEnds.push(clip.endDay);
    } else {
      laneEnds[lane] = clip.endDay;
    }
    lanes.set(promo.id, lane);
  }
  return lanes;
}

export function promoBandsByDay(
  promos: CalendarPromoAction[],
  year: number,
  month: number,
): Map<number, Array<PromoBandCell | null>> {
  const lanes = assignPromoLanes(promos, year, month);
  const laneCount = lanes.size === 0 ? 0 : Math.max(...lanes.values()) + 1;
  const map = new Map<number, Array<PromoBandCell | null>>();
  const lastDay = daysInMonth(year, month);
  for (let day = 1; day <= lastDay; day++) {
    const row: Array<PromoBandCell | null> = Array.from({ length: laneCount }, () => null);
    for (const promo of promos) {
      const cell = promoBandForDay(promo, year, month, day);
      if (!cell) continue;
      const lane = lanes.get(promo.id) ?? 0;
      cell.lane = lane;
      row[lane] = cell;
    }
    map.set(day, row);
  }
  return map;
}

export function promosOnDay(
  promos: CalendarPromoAction[],
  year: number,
  month: number,
  day: number,
): CalendarPromoAction[] {
  return promos.filter((promo) => promoBandForDay(promo, year, month, day) != null);
}
