import { describe, expect, it } from "vitest";

import {
  clipPromoToMonth,
  promoBandForDay,
  promoBandsByDay,
  type CalendarPromoAction,
} from "./promoCalendar";

const spanning: CalendarPromoAction = {
  id: 1,
  name: "Pré-venda",
  start_date: "2026-09-28",
  end_date: "2026-10-05",
  description: null,
  type_label: "Sorteio de Direito de Compra Físico",
};

describe("clipPromoToMonth", () => {
  it("clips a spanning action onto both months", () => {
    expect(clipPromoToMonth(spanning, 2026, 9)).toEqual({ startDay: 28, endDay: 30 });
    expect(clipPromoToMonth(spanning, 2026, 10)).toEqual({ startDay: 1, endDay: 5 });
    expect(clipPromoToMonth(spanning, 2026, 8)).toBeNull();
  });
});

describe("promoBandForDay", () => {
  it("covers every clipped day of the interval", () => {
    const september = [28, 29, 30].map((day) => promoBandForDay(spanning, 2026, 9, day));
    expect(september.every(Boolean)).toBe(true);
    expect(promoBandForDay(spanning, 2026, 9, 27)).toBeNull();

    const october = [1, 2, 3, 4, 5].map((day) => promoBandForDay(spanning, 2026, 10, day));
    expect(october.every(Boolean)).toBe(true);
    expect(promoBandForDay(spanning, 2026, 10, 6)).toBeNull();
  });

  it("opens the month edges when the period continues outside", () => {
    const sept30 = promoBandForDay(spanning, 2026, 9, 30);
    expect(sept30?.openRight).toBe(true);
    expect(sept30?.isEnd).toBe(true);
    expect(sept30?.showLabel).toBe(false);

    const oct1 = promoBandForDay(spanning, 2026, 10, 1);
    expect(oct1?.openLeft).toBe(true);
    expect(oct1?.isStart).toBe(true);
    expect(oct1?.showLabel).toBe(true);
  });

  it("opens week-wrap edges on Saturday and Sunday", () => {
    const weekend: CalendarPromoAction = {
      ...spanning,
      id: 2,
      start_date: "2026-09-25",
      end_date: "2026-09-28",
    };
    const saturday = promoBandForDay(weekend, 2026, 9, 26);
    const sunday = promoBandForDay(weekend, 2026, 9, 27);
    expect(saturday?.openRight).toBe(true);
    expect(saturday?.extendRight).toBe(false);
    expect(sunday?.openLeft).toBe(true);
    expect(sunday?.extendLeft).toBe(false);
  });
});

describe("promoBandsByDay", () => {
  it("keeps overlapping actions on stable lanes", () => {
    const other: CalendarPromoAction = {
      ...spanning,
      id: 2,
      name: "Outra",
      start_date: "2026-09-30",
      end_date: "2026-09-30",
    };
    const byDay = promoBandsByDay([spanning, other], 2026, 9);
    expect(byDay.get(28)?.[0]?.promo.id).toBe(1);
    expect(byDay.get(30)?.[0]?.promo.id).toBe(1);
    expect(byDay.get(30)?.[1]?.promo.id).toBe(2);
    expect(byDay.get(28)?.[1]).toBeNull();
  });
});
