import type { Match } from "../api/types";

type MatchBadgesProps = {
  match: Match;
};

/** Extra match labels (BoN lives on the tournament/round header, not per seat). */
export function MatchBadges({ match }: MatchBadgesProps) {
  if (!match.is_third_place) return null;
  return <span className="badge">3º–4º</span>;
}
