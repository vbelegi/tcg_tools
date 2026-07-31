/** Score options aligned with backend validate_score (app/core/torneios/scores.py). */

export function winsToWin(bestOf: number): number {
  return Math.floor((bestOf + 1) / 2);
}

export function isValidScorePair(
  p1: number,
  p2: number,
  bestOf: number,
  allowDraw: boolean,
): boolean {
  const maxGames = winsToWin(bestOf);
  if (p1 < 0 || p2 < 0) return false;
  if (p1 > maxGames || p2 > maxGames) return false;
  if (p1 + p2 > bestOf) return false;
  if (p1 === p2) return allowDraw;
  if (p1 < 1 && p2 < 1) return false;
  return true;
}

export function allValidScorePairs(
  bestOf: number,
  allowDraw: boolean,
): { p1: number; p2: number }[] {
  const maxGames = winsToWin(bestOf);
  const pairs: { p1: number; p2: number }[] = [];
  for (let p1 = 0; p1 <= maxGames; p1++) {
    for (let p2 = 0; p2 <= maxGames; p2++) {
      if (isValidScorePair(p1, p2, bestOf, allowDraw)) {
        pairs.push({ p1, p2 });
      }
    }
  }
  return pairs;
}

/** Scores allowed for player 1 or 2; filters by opponent when otherScore is set. */
export function validScoresForPlayer(
  bestOf: number,
  allowDraw: boolean,
  playerSide: 1 | 2,
  otherScore: number | "" | null | undefined,
): number[] {
  const pairs = allValidScorePairs(bestOf, allowDraw);
  const otherSelected =
    otherScore !== "" && otherScore !== null && otherScore !== undefined;

  const scores = new Set<number>();
  for (const p of pairs) {
    if (!otherSelected) {
      scores.add(playerSide === 1 ? p.p1 : p.p2);
    } else if (playerSide === 1 && p.p2 === otherScore) {
      scores.add(p.p1);
    } else if (playerSide === 2 && p.p1 === otherScore) {
      scores.add(p.p2);
    }
  }
  return Array.from(scores).sort((a, b) => a - b);
}

export function scoreOptionLabel(value: number, bestOf: number, allowDraw: boolean): string {
  if (allowDraw && value === 0) return "0";
  if (bestOf > 1 && value === 1) return "1 (tempo)";
  return String(value);
}
