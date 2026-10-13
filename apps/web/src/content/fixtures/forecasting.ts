import { gauss, seeded } from "@/components/figures/chart-utils";

import type { ForecastModel, ForecastModelId, ForecastResults, SensorSeries } from "../types";

// Illustrative only. Each forecast is the actual series plus smooth seeded error whose size follows the MAE table,
// so relative accuracy matches it. Never shown in a production build, and hidden once real results are published.
const HORIZONS = [15, 30, 60, 90, 120] as const;
const ORIGIN = 17 * 60;
const STEP = 15;
const PAST = 36;
const AHEAD = 8;

const MODELS: readonly ForecastModel[] = [
  { id: "persistence", name: "Persistence", mae: [3.1, 4.6, 6.9, 8.4, 9.6] },
  { id: "seasonal", name: "Daily seasonal naive", mae: [6.2, 6.3, 6.5, 6.7, 6.9] },
  { id: "gb", name: "Gradient boosting", mae: [2.4, 3.5, 5.0, 5.9, 6.6] },
  { id: "mlp", name: "Spatial MLP", mae: [2.5, 3.4, 5.1, 6.0, 6.4] },
  { id: "chronos", name: "Chronos, zero-shot", mae: [2.7, 3.7, 4.9, 5.8, 6.5] },
];
const MODEL_SEEDS: Readonly<Record<ForecastModelId, number>> = { persistence: 11, seasonal: 17, gb: 23, mlp: 37, chronos: 53 };
const SENSORS = [
  { id: "s12", label: "Sensor 12", seed: 12, base: 24, peak: 30, peakAt: 17 * 60 + 50, k: 1 },
  { id: "s47", label: "Sensor 47", seed: 47, base: 16, peak: 22, peakAt: 18 * 60 + 5, k: 0.8 },
  { id: "s103", label: "Sensor 103", seed: 103, base: 32, peak: 26, peakAt: 17 * 60 + 35, k: 1.2 },
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
    return s.base + s.peak * Math.exp(-(((m - s.peakAt) / 150) ** 2)) + 3 * Math.sin(m / 90 + s.seed) * s.k + gauss(r) * 1.2 * s.k;
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

  const built = MODELS.map((m) => [m.id, build(m)] as const);
  return {
    id: s.id,
    label: s.label,
    originMinutes: ORIGIN,
    stepMinutes: STEP,
    pastSteps: PAST,
    actual,
    forecasts: Object.fromEntries(built.map(([id, b]) => [id, b.values])) as Record<ForecastModelId, readonly number[]>,
    windowMae: Object.fromEntries(built.map(([id, b]) => [id, b.mae])) as Record<ForecastModelId, number>,
  };
}

export const forecastFixture: ForecastResults = {
  answer:
    "At 15 minutes, gradient boosting is the strongest challenger, with 23% lower error than persistence. At 2 hours, Chronos, used with no tuning, has 2% higher error than the spatial MLP.",
  keyNumbers: [
    { value: "23%", label: "lower error than persistence for gradient boosting at 15 minutes.", caveat: "95% interval 16 to 30%, from a block bootstrap over the test window." },
    { value: "2%", label: "higher error for Chronos, with no tuning, than the spatial MLP at 2 hours.", caveat: "95% interval 1 to 4%, from a block bootstrap over the test window." },
    { value: "36", label: "sensors scored at 5 horizons on the final 51 hours of data.", caveat: "One highway corridor near Washington DC, so treat the ranking as local." },
  ],
  run: { commit: "a1c9e04", manifest: "analysis/outputs/forecasting-lab-manifest.json", python: "3.12", lastRun: "2026-10-01" },
  retrieved: { "Dataset 608": "2026-09-20", "chronos-t5-small": "2026-09-21" },
  horizons: HORIZONS,
  models: MODELS,
  sensors: SENSORS.map(sensorSeries),
};
