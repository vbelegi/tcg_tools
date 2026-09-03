import { useMemo } from "react";

import { Switch } from "./Switch";

const BO_OPTIONS = [1, 3, 5] as const;

export type SeBoConfig = Record<string, number>;

type SeFormatOptionsProps = {
  thirdPlaceMatch: boolean;
  onThirdPlaceMatchChange: (value: boolean) => void;
  seBoConfig: SeBoConfig;
  onSeBoConfigChange: (value: SeBoConfig) => void;
  defaultBestOf: number;
  maxRounds: number;
  disabled?: boolean;
};

function phaseLabel(roundsFromFinal: number): string {
  if (roundsFromFinal === 1) return "Final (incl. bronze)";
  if (roundsFromFinal === 2) return "Semifinal";
  if (roundsFromFinal === 3) return "Quartas";
  if (roundsFromFinal === 4) return "Oitavas";
  if (roundsFromFinal === 5) return "Round de 16";
  return `Rodada −${roundsFromFinal}`;
}

export function SeFormatOptions({
  thirdPlaceMatch,
  onThirdPlaceMatchChange,
  seBoConfig,
  onSeBoConfigChange,
  defaultBestOf,
  maxRounds,
  disabled,
}: SeFormatOptionsProps) {
  const phases = useMemo(() => {
    const rounds = Math.max(maxRounds, 1);
    return Array.from({ length: rounds }, (_, i) => rounds - i);
  }, [maxRounds]);

  const setPhaseBo = (key: string, value: number | "") => {
    const next = { ...seBoConfig };
    if (value === "") {
      delete next[key];
    } else {
      next[key] = value;
    }
    onSeBoConfigChange(next);
  };

  return (
    <div className="card" style={{ marginTop: "1rem" }}>
      <h3>Opcões — eliminatória</h3>
      <div className="form-row">
        <Switch
          checked={thirdPlaceMatch}
          onChange={onThirdPlaceMatchChange}
          disabled={disabled}
        >
          Disputa de 3º–4º lugar (bronze)
        </Switch>
      </div>
      <p style={{ fontSize: "0.9rem", opacity: 0.85 }}>
        Melhor de por fase (vazio = herda fase seguinte ou Bo global: {defaultBestOf}). Bronze usa o
        Bo da final.
      </p>
      {phases.map((rff) => {
        const key = String(rff);
        return (
          <div className="form-row" key={key}>
            <label>{phaseLabel(rff)}</label>
            <select
              value={seBoConfig[key] ?? ""}
              onChange={(e) =>
                setPhaseBo(key, e.target.value === "" ? "" : Number(e.target.value))
              }
              disabled={disabled}
            >
              <option value="">Padrão</option>
              {BO_OPTIONS.map((bo) => (
                <option key={bo} value={bo}>
                  Bo{bo}
                </option>
              ))}
            </select>
          </div>
        );
      })}
    </div>
  );
}
