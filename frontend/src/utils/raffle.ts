/** Fisher–Yates shuffle (in-place on a copy). */
export function shuffle<T>(items: T[], random: () => number = Math.random): T[] {
  const arr = items.slice();
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

export type RaffleMode = "batch" | "chain";

export function drawWinners<T>(participants: T[], winnerCount: number): T[] {
  if (participants.length === 0) {
    throw new Error("Cadastre pelo menos um participante.");
  }
  if (!Number.isInteger(winnerCount) || winnerCount < 1) {
    throw new Error("Informe pelo menos 1 sorteado.");
  }
  if (winnerCount > participants.length) {
    throw new Error(
      `Número de sorteados (${winnerCount}) não pode ser maior que participantes (${participants.length}).`,
    );
  }
  return shuffle(participants).slice(0, winnerCount);
}

/** Sorteia um participante e devolve o restante (sem repetir). */
export function pickOne<T>(
  pool: T[],
  random: () => number = Math.random,
): { picked: T; remaining: T[] } {
  if (pool.length === 0) {
    throw new Error("Não há mais participantes para sortear.");
  }
  const idx = Math.floor(random() * pool.length);
  const picked = pool[idx];
  const remaining = pool.slice(0, idx).concat(pool.slice(idx + 1));
  return { picked, remaining };
}
