import type { Match } from "../api/types";
import { formatMatchResult } from "../utils/matches";

type RoundMatchesTableProps = {
  matches: Match[];
  title?: string;
};

export function RoundMatchesTable({ matches, title }: RoundMatchesTableProps) {
  if (matches.length === 0) return null;

  return (
    <div className="round-summary">
      {title && <h3 className="round-summary-title">{title}</h3>}
      <table>
        <thead>
          <tr>
            <th>Jogador 1</th>
            <th aria-hidden="true" />
            <th>Jogador 2</th>
            <th>Placar</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((m) => (
            <tr key={m.id}>
              <td>
                {m.is_bye ? (
                  <span className="badge">BYE — {m.player1_name}</span>
                ) : (
                  m.player1_name
                )}
              </td>
              <td className="match-vs">{!m.is_bye && "×"}</td>
              <td>
                {m.is_bye ? "—" : (m.player2_name ?? "—")}
                {m.had_rematch && (
                  <span className="badge badge-rematch" style={{ marginLeft: "0.35rem" }}>
                    Rematch
                  </span>
                )}
                {m.is_third_place && (
                  <span className="badge" style={{ marginLeft: "0.35rem" }}>
                    3º–4º
                  </span>
                )}
              </td>
              <td>
                {formatMatchResult(m)}
                {m.best_of != null && m.best_of > 1 && (
                  <span style={{ marginLeft: "0.35rem", fontSize: "0.85rem", opacity: 0.75 }}>
                    Bo{m.best_of}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
