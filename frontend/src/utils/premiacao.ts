export function sumCreditosFromRows(
  creditos: number[] | null | undefined,
  playerPayouts: Array<{ payout: number }> | undefined,
  entryFee: number,
): number | null {
  if (playerPayouts?.length) {
    return playerPayouts.reduce((sum, p) => sum + p.payout * entryFee, 0);
  }
  if (creditos?.length) {
    return creditos.reduce((sum, c) => sum + c, 0);
  }
  return null;
}

export function creditosSanityMismatch(
  totalCreditos: number | null | undefined,
  sumFromRows: number | null,
  tolerance = 0.01,
): boolean {
  if (totalCreditos == null || sumFromRows == null) return false;
  return Math.abs(totalCreditos - sumFromRows) > tolerance;
}

export function expectedTotalCreditos(jogadores: number, entryFee: number): number {
  return jogadores * entryFee;
}
