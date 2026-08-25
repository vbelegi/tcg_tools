/** Extrai nomes de texto colado (linhas, vírgulas ou ponto-e-vírgula). */
export function parsePastedNames(raw: string): string[] {
  const parts = raw
    .split(/[\n\r,;]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const seen = new Set<string>();
  const out: string[] = [];
  for (const name of parts) {
    const key = name.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(name);
  }
  return out;
}
