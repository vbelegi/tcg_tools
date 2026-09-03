import { useEffect, useState } from "react";

import { Switch } from "./Switch";

export type FilterToggle = {
  id: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
};

type Props = {
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchLabel: string;
  searchPlaceholder?: string;
  searchId?: string;
  toggles?: FilterToggle[];
  resultCount?: number;
  dateFrom?: string;
  dateTo?: string;
  onDateFromChange?: (value: string) => void;
  onDateToChange?: (value: string) => void;
  dateFromLabel?: string;
  dateToLabel?: string;
};

const DEBOUNCE_MS = 300;

/**
 * Search box plus optional date range and toggles. Typing is debounced locally so
 * every keystroke does not become a request; the parent owns the committed value.
 */
export function ListFilterBar({
  searchValue,
  onSearchChange,
  searchLabel,
  searchPlaceholder,
  searchId = "list-filter-q",
  toggles = [],
  resultCount,
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  dateFromLabel = "De",
  dateToLabel = "Até",
}: Props) {
  const [draft, setDraft] = useState(searchValue);
  const showDates = onDateFromChange != null && onDateToChange != null;

  useEffect(() => {
    setDraft(searchValue);
  }, [searchValue]);

  useEffect(() => {
    if (draft === searchValue) return;
    const timer = window.setTimeout(() => onSearchChange(draft), DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [draft, searchValue, onSearchChange]);

  return (
    <div className="list-filter-bar">
      <div className="form-row list-filter-search">
        <label htmlFor={searchId}>{searchLabel}</label>
        <input
          id={searchId}
          type="search"
          value={draft}
          placeholder={searchPlaceholder}
          onChange={(e) => setDraft(e.target.value)}
        />
      </div>
      {showDates && (
        <div className="list-filter-dates">
          <div className="form-row list-filter-date">
            <label htmlFor={`${searchId}-from`}>{dateFromLabel}</label>
            <input
              id={`${searchId}-from`}
              type="date"
              value={dateFrom ?? ""}
              onChange={(e) => onDateFromChange(e.target.value)}
            />
          </div>
          <div className="form-row list-filter-date">
            <label htmlFor={`${searchId}-to`}>{dateToLabel}</label>
            <input
              id={`${searchId}-to`}
              type="date"
              value={dateTo ?? ""}
              onChange={(e) => onDateToChange(e.target.value)}
            />
          </div>
        </div>
      )}
      {toggles.length > 0 && (
        <div className="list-filter-toggles">
          {toggles.map((toggle) => (
            <Switch key={toggle.id} checked={toggle.checked} onChange={toggle.onChange}>
              {toggle.label}
            </Switch>
          ))}
        </div>
      )}
      {resultCount != null && (
        <p className="muted list-filter-count">
          {resultCount === 1 ? "1 resultado" : `${resultCount} resultados`}
        </p>
      )}
    </div>
  );
}
