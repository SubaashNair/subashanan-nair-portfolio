import { gauss, seeded } from "@/components/figures/chart-utils";

import type { ForecastModel, ForecastModelId, ForecastResults, SensorSeries } from "../types";

// Illustrative only. Each forecast is the actual series plus smooth seeded error whose size follows the MAE table,
// so relative accuracy matches it. Never shown in a production build.
const HORIZONS = [15, 30, 60, 90, 120] as const;
const ORIGIN = 17 * 60;
const STEP = 5;
const PAST = 36;
const AHEAD = 24;

const MODELS: readonly ForecastModel[] = [
  { id: "naive", name: "Seasonal naive", mae: [9.8, 11.2, 13.5, 15.1, 16.4] },
  { id: "gb", name: "Gradient boosting", mae: [6.1, 7.9, 10.6, 12.4, 14.0] },
  { id: "gru", name: "Small neural net (GRU)", mae: [6.4, 8.1, 10.4, 12.0, 13.6] },
  { id: "chronos", name: "Chronos, zero-shot", mae: [7.0, 8.3, 10.1, 11.6, 13.4] },
];
const MODEL_SEEDS: Readonly<Record<ForecastModelId, number>> = { naive: 11, gb: 23, gru: 37, chronos: 53 };
const SENSORS = [
  { id: "s12", label: "Sensor 12", seed: 12, base: 96, peak: 82, peakAt: 17 * 60 + 50, k: 1 },
  { id: "s47", label: "Sensor 47", seed: 47, base: 64, peak: 58, peakAt: 18 * 60 + 5, k: 0.8 },
  { id: "s103", label: "Sensor 103", seed: 103, base: 128, peak: 64, peakAt: 17 * 60 + 35, k: 1.2 },
] as const;

/** MAE at any horizon in minutes, linear between the published horizons. */
function maeAt(model: ForecastModel, minutes: number): number {
  const xs = [0, ...HORIZONS];
  const ys = [model.mae[0] * 0.4, ...model.mae];
  for (let i = 1; i < xs.length; i++) {
    if (minutes <= xs[i]) return ys[i - 1] + ((ys[i] - ys[i - 1]) * (minutes - xs[i - 1])) / (xs[i] - xs[i - 1]);
  }
  return ys[ys.length - 1];
}

function sensorSeries(s: (typeof SENSORS)[number]): SensorSeries {
  const r = seeded(s.seed * 97);
  const actual = Array.from({ length: PAST + AHEAD + 1 }, (_, i) => {
    const m = ORIGIN + (i - PAST) * STEP;
    return s.base + s.peak * Math.exp(-(((m - s.peakAt) / 58) ** 2)) + 6 * Math.sin(m / 37 + s.seed) * s.k + gauss(r) * 3.2 * s.k;
  });
  const at = (t: number): number => actual[t + PAST];

  // Normalising by the weighted |z| makes each window's MAE equal k times the mean target error, so the table's ranking holds.
  const build = (model: ForecastModel): { values: readonly number[]; mae: number } => {
    const rr = seeded(MODEL_SEEDS[model.id] * 131 + s.seed);
    const zs = Array.from({ length: AHEAD }).reduce<number[]>((acc) => [...acc, 0.85 * (acc.at(-1) ?? 0) + 0.5 * gauss(rr)], []);
    const target = zs.map((_, i) => maeAt(model, (i + 1) * STEP));
    const norm = zs.reduce((a, z, i) => a + Math.abs(z) * target[i], 0) / target.reduce((a, b) => a + b, 0);
    const values = [at(0), ...zs.map((z, i) => at(i + 1) + target[i] * s.k * (z / norm))];
    const mae = values.slice(1).reduce((a, v, i) => a + Math.abs(v - at(i + 1)), 0) / AHEAD;
    return { values, mae };
  };

  const built = Object.fromEntries(MODELS.map((m) => [m.id, build(m)])) as Record<ForecastModelId, { values: readonly number[]; mae: number }>;
  return {
    id: s.id,
    label: s.label,
    originMinutes: ORIGIN,
    stepMinutes: STEP,
    pastSteps: PAST,
    actual,
    forecasts: { naive: built.naive.values, gb: built.gb.values, gru: built.gru.values, chronos: built.chronos.values },
    windowMae: { naive: built.naive.mae, gb: built.gb.mae, gru: built.gru.mae, chronos: built.chronos.mae },
  };
}

export const forecastFixture: ForecastResults = {
  answer:
    "At short horizons a tuned gradient boosting model is hard to beat. Past one hour, Chronos, used with no tuning at all, has the lowest error, about 18% below the seasonal baseline at two hours.",
  keyNumbers: [
    { value: "18%", label: "lower error for Chronos than the seasonal baseline at 2 hours.", caveat: "Interval 12 to 23%, from a bootstrap over test days." },
    { value: "4", label: "models compared on the same chronological splits.", caveat: "One dataset from one city, so treat the ranking as local." },
    { value: "0", label: "hours of tuning for Chronos.", caveat: "Its context length still caps how much history it sees." },
  ],
  run: { commit: "a1c9e04", manifest: "manifest.json", python: "3.12", lastRun: "2026-10-01" },
  retrieved: { "Dataset 608": "2026-09-20", "chronos-t5-small": "2026-09-21" },
  horizons: HORIZONS,
  models: MODELS,
  sensors: SENSORS.map(sensorSeries),
};
