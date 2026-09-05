import type { DecklistImportMeta } from "../../components/LigaMagicDeckImportFields";

export type PlacementRow = {
  player_id: number;
  name: string;
  placement: string;
  is_drop: boolean;
  decklist: string;
  deckMeta: DecklistImportMeta | null;
};


/** Reorder ranked rows; drop rows stay at the end unchanged. */
export function reorderPlacementRows(rows: PlacementRow[], fromIndex: number, toIndex: number): PlacementRow[] {
  const ranked = rows.filter((r) => !r.is_drop);
  const drops = rows.filter((r) => r.is_drop);
  if (fromIndex < 0 || fromIndex >= ranked.length || toIndex < 0 || toIndex >= ranked.length) {
    return rows;
  }
  const next = [...ranked];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  const renumbered = next.map((r, idx) => ({ ...r, placement: String(idx + 1) }));
  return [...renumbered, ...drops];
}

export function rankedRowIndices(rows: PlacementRow[]): number[] {
  return rows.map((r, i) => (r.is_drop ? -1 : i)).filter((i) => i >= 0);
}
