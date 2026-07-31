export type PlayerRecordWld = { wins: number; losses: number; draws: number };

export function formatPlayerRecord(record: PlayerRecordWld | undefined): string {
  if (!record) return "0/0/0";
  return `${record.wins}/${record.losses}/${record.draws}`;
}

export function playerRecordTitle(record: PlayerRecordWld | undefined): string {
  const wld = formatPlayerRecord(record);
  return `W/L/D: ${wld} (vitórias / derrotas / empates)`;
}
