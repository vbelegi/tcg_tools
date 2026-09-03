/**

 * API types — curated aliases; regenerate OpenAPI with `npm run generate:api`.

 */

import type { components } from "./openapi.d.ts";



type Schemas = components["schemas"];



export type Preset = Schemas["PresetBody"];

export type PresetsResponse = Schemas["PresetsResponse"] & {

  presets_updated_at?: number | null;

};

export type CalcularResponse = Schemas["CalcularResponse"];

export type TabelaLinha = Schemas["TabelaLinha"];



export interface TcgGame {
  id: number;
  name: string;
  slug: string;
  color_hex: string;
  active?: boolean;
}

export interface Torneio {
  id: number;
  name: string;
  event_date: string;
  format: "swiss" | "single_elimination";
  max_rounds: number | null;
  entry_fee: number;
  best_of: number;
  status: "draft" | "running" | "finished";
  player_count: number;
  current_round: number;
  between_rounds?: boolean;
  can_start_next_round?: boolean;
  can_finalize?: boolean;
  can_reopen_round?: boolean;
  recommended_rounds?: number;
  completed_rounds?: number;
  third_place_match?: boolean;
  se_bo_config?: Record<string, number> | null;
  config_warnings?: string[];
  players?: Player[];
  source?: "internal" | "external";
  pairing_mode?: "platform" | "manual";
  registration_open?: boolean;
  fp_n_at_start?: number | null;
  pending_checkins?: number;
  description?: string | null;
  start_time?: string | null;
  tcg_game_id?: number | null;
  tcg_game?: TcgGame | null;
  participant_user_ids?: number[];
}

export interface Player {
  id: number;
  name: string;
  seed: number | null;
  dropped_at: string | null;
  registration_order: number;
  decklist: string | null;
  user_id?: number | null;
  attendance?: "pending" | "checked_in";
  registration_source?: string;
}



export interface Match {

  id: number;

  player1_id: number;

  player1_name: string;

  player2_id: number | null;

  player2_name: string | null;

  winner_id: number | null;

  score_p1: number;

  score_p2: number;

  is_bye: boolean;

  is_walkover: boolean;

  had_rematch: boolean;

  scores_submitted?: boolean;

  is_third_place?: boolean;

  best_of?: number;

}



export interface Round {

  id: number;

  number: number;

  status: "pending" | "active" | "completed";

  player_records?: Record<number, { wins: number; losses: number; draws: number }>;

  matches: Match[];

}



export interface Standing {

  rank: number;

  player_id: number;

  name: string;

  points: number;

  omw: number;

  gw: number;

  ogw: number;

  decklist: string | null;

  is_drop?: boolean;

  rank_label?: string | null;

}

export interface ProfileHistoryRow {
  event_id: number;
  event_name: string;
  event_date: string;
  source: string;
  rank: number | null;
  rank_label: string | null;
  is_drop: boolean;
  decklist: string | null;
  player_count: number;
  tcg_game: TcgGame | null;
  fp_earned: number;
}

export interface PromoRegulation {
  version: number;
  display_name: string;
  url: string;
  uploaded_at?: string | null;
  uploaded_by_user_id?: number | null;
}

export interface PromoActionType {
  key: string;
  label: string;
}

export interface PromoAction {
  id: number;
  name: string;
  type: string;
  type_label: string;
  start_date: string;
  end_date: string;
  description: string | null;
  published: boolean;
  show_in_calendar: boolean;
  max_participants: number | null;
  regulation: PromoRegulation | null;
  created_at: string | null;
  /** Detail only. */
  how_to_participate?: string | null;
  management_panel_key?: string | null;
  /** Staff only — never sent to players or guests. */
  participant_count?: number;
  regulation_versions?: PromoRegulation[];
}

export interface PlayerProfile {
  id: number;
  display_name: string;
  role: string;
  status: string;
  created_at: string | null;
  avatar_url: string | null;
  fourse_points: number | null;
  fourse_points_visible: boolean;
  ranking_position: number | null;
  can_edit: boolean;
  viewer_authenticated: boolean;
  stats: {
    tournaments: number;
    titles: number;
    top8: number;
    best_finish: number | null;
  };
  insights: string[];
  badge_games: TcgGame[];
  fp_by_game: Array<{
    tcg_name: string;
    tcg_game: TcgGame | null;
    points: number;
    tournaments: number;
  }>;
  fp_by_month: Array<{ month: string; points: number; tournaments: number }>;
  history: ProfileHistoryRow[];
}


