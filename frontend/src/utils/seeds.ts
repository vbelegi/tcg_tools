/** Se algum jogador tem seed, retorna os que estão sem (all-or-nothing). */
export function playersMissingSeed<T extends { seed: number | null | undefined }>(
  players: T[],
): T[] {
  const hasAny = players.some((p) => p.seed != null);
  if (!hasAny) return [];
  return players.filter((p) => p.seed == null);
}

export function seedRequirementMessage(missingNames: string[]): string {
  if (missingNames.length === 0) return "";
  return (
    "Seeding parcial: informe seed para todos os jogadores, ou deixe todos sem seed. " +
    `Faltando seed: ${missingNames.join(", ")}.`
  );
}
