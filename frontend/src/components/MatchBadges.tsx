import type { Match } from "../api/types";

type MatchBadgesProps = {
  match: Match;
  bestOf: number;
};

export function MatchBadges({ match, bestOf }: MatchBadgesProps) {
  return (
    <>
      {match.is_third_place && (
        <span className="badge" style={{ marginLeft: "0.35rem" }}>
          3º–4º
        </span>
      )}
      {bestOf > 1 && (
        <span style={{ marginLeft: "0.35rem", fontSize: "0.85rem", opacity: 0.75 }}>
          Bo{bestOf}
        </span>
      )}
    </>
  );
}
