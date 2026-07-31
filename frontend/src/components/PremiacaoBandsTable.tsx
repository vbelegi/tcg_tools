export type PremiacaoBandRow = {
  label: string;
  pool: number;
  tier_indices?: number[];
  player_count?: number;
  payout_per_player?: number | null;
};

export type PlayerPayoutRow = {
  player_id: number;
  name: string;
  band_label: string;
  payout: number;
};

type PremiacaoBandsTableProps = {
  bands: PremiacaoBandRow[];
  playerPayouts?: PlayerPayoutRow[];
  creditos?: number[] | null;
  bandCreditos?: number[] | null;
  entryFee?: number;
};

export function PremiacaoBandsTable({
  bands,
  playerPayouts,
  bandCreditos,
  entryFee,
}: PremiacaoBandsTableProps) {
  const showCreditos = (entryFee ?? 0) > 0;

  if (playerPayouts && playerPayouts.length > 0) {
    return (
      <table>
        <thead>
          <tr>
            <th>Faixa</th>
            <th>Jogador</th>
            <th>Inscrições</th>
            {showCreditos && <th>Créditos na Loja</th>}
          </tr>
        </thead>
        <tbody>
          {playerPayouts.map((p) => (
            <tr key={p.player_id}>
              <td>{p.band_label}</td>
              <td>{p.name}</td>
              <td>{p.payout}</td>
              {showCreditos && (
                <td>R$ {((p.payout * (entryFee ?? 0)) || 0).toFixed(2)}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Faixa</th>
          <th>Pool (inscrições)</th>
          <th>Por jogador (esperado)</th>
          {showCreditos && bandCreditos && <th>Créditos / jogador</th>}
        </tr>
      </thead>
      <tbody>
        {bands.map((b, i) => (
          <tr key={b.label}>
            <td>{b.label}</td>
            <td>{b.pool.toFixed(2)}</td>
            <td>{b.payout_per_player != null ? b.payout_per_player.toFixed(2) : "—"}</td>
            {showCreditos && bandCreditos && (
              <td>
                {b.payout_per_player != null
                  ? `R$ ${(bandCreditos[i] ?? 0).toFixed(2)}`
                  : "—"}
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
