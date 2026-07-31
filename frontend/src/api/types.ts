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

}



export interface Player {

  id: number;

  name: string;

  seed: number | null;

  dropped_at: string | null;

  registration_order: number;

  decklist: string | null;

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


