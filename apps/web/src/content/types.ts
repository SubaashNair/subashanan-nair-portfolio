import type { Ground, TileSpec } from "@/components/tiles/tile-geometry";

export type StudySlug = "penang-pulse" | "forecasting-lab" | "llm-eval-lab";
export type StudyStatus = "published" | "in-progress" | "planned";
export type ThemeClass = "s-pulse" | "s-forecast" | "s-llm";

export interface Source {
  name: string;
  publisher: string;
  used: string;
  licence: string;
}

export interface StudyRecord {
  slug: StudySlug;
  title: string;
  question: string;
  status: StudyStatus;
  plannedAnswer: string; // shown when no results exist; contains no numbers
  figurePlan: string; // what the evidence chapter will show
  data: string; // one line for cards
  tile: TileSpec;
  tint: Ground;
  themeClass: ThemeClass;
  sources: readonly Source[];
  method: readonly string[];
  limitations: readonly string[];
  reproduce: { commands: readonly string[]; note?: string };
  discussNote: string;
}

export interface KeyNumber {
  value: string;
  label: string;
  caveat: string;
}

export interface RunInfo {
  commit: string;
  manifest: string;
  python: string;
  lastRun: string; // ISO date
}

export interface BaseResults {
  answer: string;
  keyNumbers: readonly [KeyNumber, KeyNumber, KeyNumber];
  run: RunInfo;
  retrieved: Readonly<Record<string, string>>; // source name to ISO date
}

export type ServiceCategory = "clinic" | "school" | "transit";
export interface District {
  id: string;
  name: string;
  short: string;
  bands: readonly [number, number, number]; // % under 1 km, 1 to 3 km, over 3 km
  population: number;
}
export interface ServicePoint {
  category: ServiceCategory;
  x: number;
  y: number;
}
export interface MapLabel {
  text: string;
  x: number;
  y: number;
}
export interface PenangGeometry {
  island: string;
  mainland: string;
  districts: ReadonlyArray<{ id: string; d: string; land: "island" | "mainland" }>;
  boundaries: readonly string[];
  bridges: readonly string[];
  places: readonly MapLabel[];
  water: MapLabel;
}
export interface PenangResults extends BaseResults {
  districts: readonly District[];
  points: readonly ServicePoint[];
  geometry: PenangGeometry;
  pointsNote: string;
}

export type ForecastModelId = "naive" | "gb" | "gru" | "chronos";
export interface ForecastModel {
  id: ForecastModelId;
  name: string;
  mae: readonly number[]; // one value per horizon
}
export interface SensorSeries {
  id: string;
  label: string;
  originMinutes: number; // minutes after midnight at the forecast origin
  stepMinutes: number;
  pastSteps: number;
  actual: readonly number[]; // pastSteps + aheadSteps + 1 values, origin at index pastSteps
  forecasts: Readonly<Record<ForecastModelId, readonly number[]>>; // aheadSteps + 1 values, index 0 is the origin
  windowMae: Readonly<Record<ForecastModelId, number>>;
}
export interface ForecastResults extends BaseResults {
  horizons: readonly number[];
  models: readonly ForecastModel[];
  sensors: readonly SensorSeries[];
}

export type ModelRole = "frontier" | "ft" | "open" | "base";
export interface EvalRow {
  model: string;
  role: ModelRole;
  score: number;
  low: number;
  high: number;
  costPer1k: number;
  costLabel: string;
  latency: string;
}
export interface EvalTask {
  id: string;
  label: string;
  metric: string;
  rows: readonly EvalRow[];
}
export interface ErrorExample {
  input: string;
  expected: string;
  model: string;
  output: string;
  note: string;
  correct: boolean;
}
export interface LlmEvalResults extends BaseResults {
  tasks: readonly EvalTask[];
  errorExamples: readonly ErrorExample[];
}

export interface StudyResultsBySlug {
  "penang-pulse": PenangResults;
  "forecasting-lab": ForecastResults;
  "llm-eval-lab": LlmEvalResults;
}

export type ExperimentCategory = "agents" | "libraries" | "apps" | "ml";
export interface ExperimentRecord {
  name: string;
  category: ExperimentCategory;
  language: string;
  description: string;
  tile: number; // index for mixedTile
}
