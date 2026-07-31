import type { Match } from "../api/types";

export type ScoreDraft = { p1: string; p2: string };

export function isMatchIncomplete(match: Match): boolean {
  if (match.is_bye || match.is_walkover) return false;
  if (match.scores_submitted) return false;
  return true;
}

export function incompleteMatches(matches: Match[]): Match[] {
  return matches.filter((m) => isMatchIncomplete(m));
}

export function matchSummaryLabel(match: Match): string {
  if (match.is_bye) return `BYE — ${match.player1_name}`;
  if (match.is_walkover) {
    return `${match.player1_name} × ${match.player2_name ?? "?"}`;
  }
  return `${match.player1_name} × ${match.player2_name ?? "?"}`;
}

export function formatMatchResult(match: Match): string {
  if (match.is_bye) return "BYE";
  if (match.is_walkover) return `${match.score_p1}–${match.score_p2} (WO)`;
  if (!match.scores_submitted) return "—";
  return `${match.score_p1}–${match.score_p2}`;
}
