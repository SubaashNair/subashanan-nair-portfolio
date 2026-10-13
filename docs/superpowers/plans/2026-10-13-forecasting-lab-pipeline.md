# Forecasting Lab Real-Results Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Forecasting Lab's illustrative fixture with real results: a tested Python pipeline over UCI dataset 608 writes one validated results file, the site publishes it, and the CV quotes it.

**Architecture:** A uv-managed Python 3.12 workspace in `analysis/` holds the package `forecasting/` (data, features, models, chronos_adapter, evaluate, pipeline, export, cli). `pipeline.run` is pure and is tested end to end on a synthetic file with a fake Chronos, so CI never installs PyTorch. The CLI downloads the data, runs five models, and writes `apps/web/src/content/results/forecasting-lab.json` plus a manifest. The web app validates that file with a hand-written guard at import time, so a bad file fails `next build`.

**Tech Stack:** Python 3.12, uv 0.11.4, numpy, scipy, scikit-learn, pytest; optional group `chronos` (chronos-forecasting 2.3.2, torch). Next.js 16.4, React 19.2, TypeScript 5.9, Vitest 4. PyMuPDF 1.26.7 for the CV, run with `uv run --no-project --with`.

**Spec:** `docs/superpowers/specs/2026-10-13-forecasting-lab-pipeline-design.md`. Brief: `.context/forecasting-planning-brief.md`.

## Global Constraints

- Honesty rule: no invented numbers anywhere. Every number on the site and in the CV comes from `apps/web/src/content/results/forecasting-lab.json`, which only the pipeline writes. Only `apps/web/src/lib/study-results.ts` branches on `NODE_ENV`.
- Copy rules: sentence case, no em or en dashes in prose, no arrows, no all-caps labels.
- Files under 400 lines. Immutable patterns in TypeScript (never mutate props, state or imported data). Python is typed, with small functions.
- Never commit raw data (`analysis/data/raw/` is git-ignored), model weights, `.env*`, `.vercel/`, `analysis/.venv/` or the full CV.
- Chronos and PyTorch live only in the uv group `chronos`. Plain `uv sync`, `uv run pytest` and CI never install them.
- Web checks from the repository root: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`. One web test file: `npm test --workspace web -- src/path/to/file.test.ts`. Python checks from `analysis/`: `uv run pytest`.
- `apps/web/AGENTS.md` applies to web code: read the relevant guide in `node_modules/next/dist/docs/` before using a Next.js API.
- Every test is written first and seen to fail before the code that makes it pass.
- Work on branch `codebase-review-plan`. One conventional commit per task.

## Review Focus

1. **No leakage.** No training target, tuning choice or fitted statistic uses validation or test values, and no feature reads past its origin. Tests: Task 3 (`test_split_is_ordered_contiguous_and_non_overlapping`), Task 4 (`test_no_feature_uses_values_after_its_origin`), Task 5 (`test_training_targets_stay_inside_the_training_block`, `test_mlp_scaler_statistics_come_from_training_rows_only`).
2. **No hand-typed numbers.** The answer, key numbers and CV bullet come from templates over computed values. Tests: Task 9 (`test_templates_say_lower_or_higher_from_the_sign`, `test_numbers_are_scaled_computed_values`), Task 13 (`test_forecast_text_uses_only_numbers_from_the_results`). Check: Task 12, Step 7 compares the page with the JSON.
3. **A malformed results file fails the build.** Tests: Task 2 (twelve malformed cases). Check: Task 12, Step 5 breaks the file on purpose and watches `npm run build` fail.
4. **CI never installs PyTorch.** Check: Task 10 CI job runs `uv sync --locked` with no group. Test: Task 6 (`test_importing_the_adapter_does_not_import_torch`).
5. **The charts are right for 15-minute data.** Clock labels wrap across midnight, hour ticks every 4 steps, the error axis fits the data, no negative flow axis. Tests: Task 1. Check: Task 12, Step 8 screenshots.
6. **The full CV never enters git.** Check: Task 13, Step 6 (`git check-ignore`).

## Before you start

- Commit the spec and this plan if they are still uncommitted: `git add docs/superpowers && git commit -m "docs: add Forecasting Lab pipeline spec and plan"`.
- `apps/web/next-env.d.ts` flips between `./.next/dev/types/...` and `./.next/types/...` whenever `next dev` or `next build` runs. Never stage it. Restore it with `git checkout -- apps/web/next-env.d.ts` before Task 11, which needs a clean tree.
- uv 0.11.4 is installed. Python 3.12 is not on the PATH; uv downloads it on the first `uv sync` because `pyproject.toml` requires `>=3.12,<3.13`.

## File map

```
.github/workflows/ci.yml                               add the analysis job (Task 10)
analysis/
  pyproject.toml, uv.lock                              workspace, groups dev and chronos (Task 3)
  forecasting/__init__.py, data.py                     download, checksums, load, calendar check, split (Task 3)
  forecasting/features.py                              lags, neighbour means, calendar features (Task 4)
  forecasting/models.py                                persistence, seasonal, tuned gb and mlp (Task 5)
  forecasting/chronos_adapter.py                       Chronos zero-shot, torch imported lazily (Task 6)
  forecasting/evaluate.py                              MAE and block bootstrap (Task 7)
  forecasting/pipeline.py                              runs and scores every model (Task 8)
  forecasting/export.py                                results JSON, templates (Task 9)
  forecasting/cli.py                                   entry point and manifest (Task 10)
  tools/update_cv.py                                   CV PDF editor (Task 13)
  tests/__init__.py, conftest.py                       synthetic .mat fixture (Tasks 3 and 8)
  tests/fakes.py                                       QUICK settings and FakeChronos (Tasks 5 and 6)
  tests/test_data.py, test_features.py, test_models.py, test_chronos_adapter.py, test_evaluate.py,
  tests/test_pipeline.py, test_export.py, test_cli.py, test_update_cv.py
  outputs/forecasting-lab-manifest.json                written by the real run (Task 11)
apps/web/
  public/subashanan-nair-cv.pdf                        updated (Task 13)
  src/content/types.ts                                 five model ids (Task 1)
  src/content/fixtures/forecasting.ts                  15-minute illustrative fixture (Task 1)
  src/content/content.test.ts                          fixture tests (Task 1)
  src/content/studies.ts                               Forecasting Lab record (Task 12)
  src/content/results/parse-forecast.ts, .test.ts      validator (Task 2)
  src/content/results/forecasting-lab.json             written by the real run (Task 11)
  src/content/results/index.ts, index.test.ts          publish the validated file (Task 12)
  src/components/figures/chart-utils.ts, .test.ts      clock wrap, niceStep (Task 1)
  src/components/figures/forecasting/model-style.ts, model-style.test.ts   (Task 1)
  src/components/figures/forecasting/forecast-chart.tsx, horizon-chart.tsx, forecast-figure.tsx, forecast-figure.test.tsx   (Task 1)
  src/components/study/chapters.tsx                    key numbers keyed by label (Task 12)
  src/lib/study-results.test.ts                        published results win (Task 12)
```

Not committed: `analysis/data/raw/`, `analysis/.venv/`, `.context/resume/`.

---

### Task 1: Web: five forecasting models on 15-minute steps

**Files:**
- Modify: `apps/web/src/content/types.ts`, `apps/web/src/components/figures/chart-utils.ts`, `apps/web/src/components/figures/forecasting/forecast-chart.tsx`, `horizon-chart.tsx`, `forecast-figure.tsx`
- Replace: `apps/web/src/components/figures/forecasting/model-style.ts`, `apps/web/src/content/fixtures/forecasting.ts`
- Test: `apps/web/src/components/figures/chart-utils.test.ts` (replace), `apps/web/src/components/figures/forecasting/model-style.test.ts` (create), `forecast-figure.test.tsx` (replace), `apps/web/src/content/content.test.ts` (modify)

**Interfaces:**
- Consumes: `palette` (`@/styles/palette`), `contrastRatio(a, b)` (`@/styles/contrast`), `gauss`, `seeded` (`chart-utils`).
- Produces: `type ForecastModelId = "persistence" | "seasonal" | "gb" | "mlp" | "chronos"`; `MODEL_STYLE: Readonly<Record<ForecastModelId, { colour: string; dash?: string }>>`; `clock(minutes: number): string` that wraps across midnight; `niceStep(raw: number): number`; `forecastFixture: ForecastResults` with `stepMinutes` 15, `pastSteps` 36 and 8 steps ahead. Task 2 uses the fixture as its valid input.

- [ ] **Step 1: Write the failing tests**

Replace `apps/web/src/components/figures/chart-utils.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { clock, niceStep, pathOf, scale, seeded } from "./chart-utils";

describe("chart utils", () => {
  it("maps a domain onto a range, including reversed ranges", () => {
    const y = scale(0, 10, 100, 0);
    expect(y(0)).toBe(100);
    expect(y(5)).toBe(50);
    expect(y(10)).toBe(0);
  });

  it("gives the same sequence for the same seed", () => {
    const a = seeded(7);
    const b = seeded(7);
    expect([a(), a(), a()]).toEqual([b(), b(), b()]);
  });

  it("builds an SVG path", () => {
    expect(pathOf([[0, 0], [10.04, 5]])).toBe("M0.0 0.0L10.0 5.0");
  });

  it("formats minutes after midnight as a clock", () => {
    expect(clock(17 * 60 + 5)).toBe("17:05");
  });

  it("wraps clock times across midnight", () => {
    expect(clock(-45)).toBe("23:15");
    expect(clock(24 * 60 + 30)).toBe("00:30");
  });

  it("picks round tick steps", () => {
    expect([niceStep(0.21), niceStep(0.7), niceStep(2), niceStep(3), niceStep(5.47), niceStep(30)]).toEqual([0.25, 1, 2, 5, 10, 50]);
    expect(niceStep(0)).toBe(1);
  });
});
```

Create `apps/web/src/components/figures/forecasting/model-style.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { contrastRatio } from "@/styles/contrast";
import { palette } from "@/styles/palette";

import { MODEL_STYLE } from "./model-style";

const styles = Object.entries(MODEL_STYLE);

describe("MODEL_STYLE", () => {
  it("styles exactly the five models", () => {
    expect(Object.keys(MODEL_STYLE)).toEqual(["persistence", "seasonal", "gb", "mlp", "chronos"]);
  });

  it("gives every model its own colour", () => {
    expect(new Set(styles.map(([, s]) => s.colour)).size).toBe(5);
  });

  it.each(styles)("%s is at least 3:1 on porcelain and sky", (_id, style) => {
    expect(contrastRatio(style.colour, palette.porcelain)).toBeGreaterThanOrEqual(3);
    expect(contrastRatio(style.colour, palette.sky)).toBeGreaterThanOrEqual(3);
  });

  it("dashes only the persistence baseline", () => {
    expect(styles.filter(([, s]) => s.dash).map(([id]) => id)).toEqual(["persistence"]);
  });
});
```

Replace `apps/web/src/components/figures/forecasting/forecast-figure.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { forecastFixture } from "@/content/fixtures/forecasting";
import type { ForecastModelId } from "@/content/types";

import { ForecastFigure } from "./forecast-figure";
import { HorizonChart } from "./horizon-chart";

describe("ForecastFigure", () => {
  it("server-renders both charts with every model line", () => {
    const html = renderToStaticMarkup(<ForecastFigure data={forecastFixture} />);
    expect(html).toContain("Traffic flow for Sensor 12");
    expect((html.match(/class="model-line"/g) ?? []).length).toBe(10); // 5 forecast lines and 5 horizon lines
  });

  it("switches sensor and updates the window error list", () => {
    render(<ForecastFigure data={forecastFixture} />);
    const before = screen.getByRole("list", { name: /mean absolute error in this window/i }).textContent;
    fireEvent.click(screen.getByRole("tab", { name: "Sensor 47" }));
    expect(screen.getByRole("img", { name: /sensor 47/i })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: /mean absolute error in this window/i }).textContent).not.toBe(before);
  });

  it("hides a model from both charts", () => {
    const { container } = render(<ForecastFigure data={forecastFixture} />);
    fireEvent.click(screen.getByRole("button", { name: "Chronos, zero-shot" }));
    expect(container.querySelectorAll(".model-line")).toHaveLength(8);
  });

  it("bolds the lowest error in each horizon column", () => {
    render(<ForecastFigure data={forecastFixture} />);
    const bold = screen.getByRole("table").querySelectorAll("b");
    expect([...bold].map((b) => b.textContent)).toEqual(["2.4", "3.4", "6.4", "4.9", "5.8"]); // row order: gb, mlp, chronos
  });

  it("labels the time axis every hour for 15 minute steps, across midnight", () => {
    const sensor = { ...forecastFixture.sensors[0], originMinutes: 60 };
    const html = renderToStaticMarkup(<ForecastFigure data={{ ...forecastFixture, sensors: [sensor] }} />);
    expect(html).toContain(">16:00<");
    expect(html).toContain(">00:00<");
    expect(html).toContain(">03:00<");
  });

  it("starts the flow axis at zero for a quiet sensor", () => {
    const s = forecastFixture.sensors[0];
    const quiet = (values: readonly number[]): number[] => values.map((v) => v / 10);
    const forecasts = Object.fromEntries(Object.entries(s.forecasts).map(([id, values]) => [id, quiet(values)])) as Record<ForecastModelId, number[]>;
    const html = renderToStaticMarkup(<ForecastFigure data={{ ...forecastFixture, sensors: [{ ...s, actual: quiet(s.actual), forecasts }] }} />);
    expect(html).not.toContain(">-25<");
    expect(html).toContain('text-anchor="end">0<');
  });

  it("scales the error axis to the largest error", () => {
    const models = [{ id: "gb" as const, name: "Gradient boosting", mae: [12, 18, 24, 31, 38] }];
    const html = renderToStaticMarkup(<HorizonChart horizons={forecastFixture.horizons} models={models} visible={new Set(["gb"])} />);
    expect([...html.matchAll(/text-anchor="end">([\d.]+)</g)].map((m) => m[1])).toEqual(["0", "20", "40"]);
  });
});
```

In `apps/web/src/content/content.test.ts`, replace the two forecasting tests inside `describe("fixtures", ...)`:

```ts
  it("gives every forecast series the right length", () => {
    const f = fixtures["forecasting-lab"]!;
    for (const s of f.sensors) {
      expect(s.actual.length).toBe(s.pastSteps + 25);
      for (const m of f.models) expect(s.forecasts[m.id].length).toBe(25);
    }
  });

  it("keeps the seasonal baseline worst in every sensor window", () => {
    for (const s of fixtures["forecasting-lab"]!.sensors) {
      const others = (["gb", "gru", "chronos"] as const).map((id) => s.windowMae[id]);
      expect(s.windowMae.naive).toBeGreaterThan(Math.max(...others));
    }
  });
```

with:

```ts
  it("gives every forecast series the right length", () => {
    const f = fixtures["forecasting-lab"]!;
    for (const s of f.sensors) {
      expect(s.stepMinutes).toBe(15);
      expect(s.actual.length).toBe(s.pastSteps + 9);
      for (const m of f.models) expect(s.forecasts[m.id].length).toBe(9);
    }
  });

  it("keeps persistence worst in every sensor window", () => {
    for (const s of fixtures["forecasting-lab"]!.sensors) {
      const others = (["seasonal", "gb", "mlp", "chronos"] as const).map((id) => s.windowMae[id]);
      expect(s.windowMae.persistence).toBeGreaterThan(Math.max(...others));
    }
  });
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/components/figures src/content/content.test.ts`
Expected: FAIL. Among the failures: `niceStep is not a function` and `expected '-1:-45' to be '23:15'` in `chart-utils.test.ts`; the model-style key list differs; the figure test counts 8 model lines, not 10; `expected 5 to be 15` for `stepMinutes`.

- [ ] **Step 3: Implement**

In `apps/web/src/content/types.ts`, replace:

```ts
export type ForecastModelId = "naive" | "gb" | "gru" | "chronos";
```

with:

```ts
export type ForecastModelId = "persistence" | "seasonal" | "gb" | "mlp" | "chronos";
```

Replace `apps/web/src/components/figures/chart-utils.ts`:

```ts
export const scale =
  (d0: number, d1: number, r0: number, r1: number) =>
  (v: number): number =>
    r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

/** Park-Miller generator, so illustrative data is stable between renders. */
export function seeded(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return s / 2147483647;
  };
}

/** Roughly normal noise with unit spread, from four uniform draws. */
export const gauss = (rand: () => number): number => (rand() + rand() + rand() + rand() - 2) * 1.73;

export const pathOf = (points: ReadonlyArray<readonly [number, number]>): string =>
  points.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join("");

const DAY_MINUTES = 24 * 60;

/** Minutes after midnight as a 24-hour clock. Values before midnight or past the end of the day wrap around. */
export const clock = (minutes: number): string => {
  const m = ((minutes % DAY_MINUTES) + DAY_MINUTES) % DAY_MINUTES;
  return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
};

/** The smallest of 1, 2, 2.5 or 5 times a power of ten that is at least `raw`, for evenly spaced axis ticks. */
export function niceStep(raw: number): number {
  if (!(raw > 0)) return 1;
  const power = 10 ** Math.floor(Math.log10(raw));
  const factor = [1, 2, 2.5, 5, 10].find((f) => f * power >= raw * (1 - 1e-9)) ?? 10;
  return Number((factor * power).toPrecision(6));
}
```

Replace `apps/web/src/components/figures/forecasting/model-style.ts`:

```ts
import type { ForecastModelId } from "@/content/types";
import { palette } from "@/styles/palette";

// One colour per model across both charts, the toggles and the table. All are at least 3:1 on porcelain and sky.
export const MODEL_STYLE: Readonly<Record<ForecastModelId, { colour: string; dash?: string }>> = {
  persistence: { colour: palette.inkSoft, dash: "7 5" },
  seasonal: { colour: palette.roseDeep },
  gb: { colour: palette.mustardDeep },
  mlp: { colour: palette.cobalt },
  chronos: { colour: palette.jadeDeep },
};
```

Replace `apps/web/src/content/fixtures/forecasting.ts`:

```ts
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
```

Replace `apps/web/src/components/figures/forecasting/forecast-chart.tsx`:

```tsx
"use client";

import { useRef } from "react";

import type { ForecastModel, SensorSeries } from "@/content/types";
import { palette } from "@/styles/palette";

import { clock, pathOf, scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { MODEL_STYLE } from "./model-style";

interface ForecastChartProps {
  sensor: SensorSeries;
  models: readonly ForecastModel[];
  visible: ReadonlySet<string>;
}

export function ForecastChart({ sensor, models, visible }: ForecastChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(420, Math.max(300, w * 0.52)));
  const pad = { l: 46, r: 14, t: 34, b: 38 };
  const past = sensor.pastSteps;
  const ahead = sensor.actual.length - past - 1;
  const shown = models.filter((m) => visible.has(m.id));
  const values = [...sensor.actual, ...shown.flatMap((m) => sensor.forecasts[m.id])];
  const min = Math.min(...values);
  // Pad below the lowest value, but not past zero unless a value is negative.
  const lo = Math.floor((min >= 0 ? Math.max(0, min - 5) : min - 5) / 25) * 25;
  const hi = Math.ceil((Math.max(...values) + 5) / 25) * 25;
  const x = scale(-past, ahead, pad.l, w - pad.r);
  const y = scale(lo, hi, h - pad.b, pad.t);
  const yTicks = Array.from({ length: (hi - lo) / 25 + 1 }, (_, i) => lo + i * 25);
  const hourStep = (w < 520 ? 120 : 60) / sensor.stepMinutes;
  const xTicks = Array.from({ length: Math.floor((past + ahead) / hourStep) + 1 }, (_, i) => -past + i * hourStep);

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`Traffic flow for ${sensor.label}, actual and forecast, flow index per ${sensor.stepMinutes} minutes`}>
        <rect x={x(0)} y={pad.t} width={x(ahead) - x(0)} height={h - pad.b - pad.t} fill={palette.sky} />
        <text className="strong" x={x(0) + 8} y={pad.t - 12}>Next 2 hours</text>
        {yTicks.map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {xTicks.map((t) => <text key={t} x={x(t)} y={h - pad.b + 22} textAnchor="middle">{clock(sensor.originMinutes + t * sensor.stepMinutes)}</text>)}
        <line x1={x(0)} x2={x(0)} y1={pad.t} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        <line x1={pad.l} x2={w - pad.r} y1={h - pad.b} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        <path d={pathOf(sensor.actual.map((v, i) => [x(i - past), y(v)] as const))} fill="none" stroke={palette.ink} strokeWidth={2.5} strokeLinejoin="round" />
        {shown.map((m) => (
          <path
            key={m.id}
            className="model-line"
            d={pathOf(sensor.forecasts[m.id].map((v, i) => [x(i), y(v)] as const))}
            fill="none"
            stroke={MODEL_STYLE[m.id].colour}
            strokeWidth={2.75}
            strokeLinejoin="round"
            strokeDasharray={MODEL_STYLE[m.id].dash}
          />
        ))}
      </svg>
    </div>
  );
}
```

Replace `apps/web/src/components/figures/forecasting/horizon-chart.tsx`:

```tsx
"use client";

import { useRef } from "react";

import type { ForecastModel } from "@/content/types";
import { palette } from "@/styles/palette";

import { niceStep, pathOf, scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { MODEL_STYLE } from "./model-style";

interface HorizonChartProps {
  horizons: readonly number[];
  models: readonly ForecastModel[];
  visible: ReadonlySet<string>;
}

export function HorizonChart({ horizons, models, visible }: HorizonChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(340, Math.max(260, w * 0.42)));
  const pad = { l: 40, r: 18, t: 18, b: 40 };
  const x = (i: number): number => pad.l + 20 + i * ((w - pad.l - pad.r - 40) / (horizons.length - 1));
  const top = Math.max(...models.flatMap((m) => m.mae));
  const step = niceStep(top / 3);
  const ticks = Array.from({ length: Math.max(1, Math.ceil(top / step)) + 1 }, (_, i) => Number((i * step).toPrecision(6)));
  const y = scale(0, ticks[ticks.length - 1], h - pad.b, pad.t);

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Mean absolute error by forecast horizon for each model">
        {ticks.map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={v ? 0.1 : 1} strokeWidth={v ? 1 : 1.5} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {horizons.map((hz, i) => <text key={hz} x={x(i)} y={h - pad.b + 22} textAnchor="middle">{hz} min</text>)}
        {models.filter((m) => visible.has(m.id)).map((m) => (
          <g key={m.id}>
            <path className="model-line" d={pathOf(m.mae.map((v, i) => [x(i), y(v)] as const))} fill="none" stroke={MODEL_STYLE[m.id].colour} strokeWidth={2.75} strokeDasharray={MODEL_STYLE[m.id].dash} />
            {m.mae.map((v, i) => <circle key={i} cx={x(i)} cy={y(v)} r={4.5} fill={MODEL_STYLE[m.id].colour} stroke="#fff" strokeWidth={1.5} />)}
          </g>
        ))}
      </svg>
    </div>
  );
}
```

In `apps/web/src/components/figures/forecasting/forecast-figure.tsx`, replace:

```tsx
          <figcaption className="figcap">Vehicles per 5 minutes. The shaded window is the forecast; the seasonal naive line is dashed.</figcaption>
```

with:

```tsx
          <figcaption className="figcap">Flow index per {sensor.stepMinutes} minutes, where 100 is the busiest reading in the dataset. The shaded window is the forecast; the persistence line is dashed. Clock times are the dataset&apos;s own.</figcaption>
```

and replace:

```tsx
          <p className="figcap" style={{ margin: "0 0 14px" }}>Mean absolute error on the test window, all sensors, vehicles per 5 minutes. Lower is better.</p>
```

with:

```tsx
          <p className="figcap" style={{ margin: "0 0 14px" }}>Mean absolute error on the test window, all sensors, in flow index points. Lower is better.</p>
```

- [ ] **Step 4: Run the tests and checks**

Run: `npm test`, then `npm run typecheck` and `npm run lint`.
Expected: `Tests  103 passed (103)` (90 before this task, plus 13), and typecheck and lint print no errors. Then run `grep -rn '"naive"\|"gru"\|gru:\|naive:' apps/web/src`. Expected: no matches.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/content/types.ts apps/web/src/content/fixtures/forecasting.ts apps/web/src/content/content.test.ts apps/web/src/components/figures
git commit -m "feat: show five forecasting models on 15 minute steps"
```

---

### Task 2: Web: validate Forecasting Lab results files

**Files:**
- Create: `apps/web/src/content/results/parse-forecast.ts`
- Test: `apps/web/src/content/results/parse-forecast.test.ts`

**Interfaces:**
- Consumes: `ForecastResults`, `ForecastModelId` (`content/types.ts`, Task 1); `forecastFixture` as the valid example (Task 1).
- Produces: `parseForecastResults(json: unknown): ForecastResults`. It returns its input, typed, when every check passes, and otherwise throws `Error("forecasting-lab results: <path> <problem>")` naming the first bad field. Task 12 calls it on the committed JSON.

- [ ] **Step 1: Write the failing test**

`apps/web/src/content/results/parse-forecast.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { forecastFixture } from "../fixtures/forecasting";
import { parseForecastResults } from "./parse-forecast";

// The fixture, as plain JSON, is a valid file. Each malformed case changes one thing in a copy.
const valid = JSON.parse(JSON.stringify(forecastFixture));
const sensor = valid.sensors[0];
const withSensor = (changes: object) => ({ ...valid, sensors: [{ ...sensor, ...changes }, ...valid.sensors.slice(1)] });

describe("parseForecastResults", () => {
  it("accepts a valid file and returns its data", () => {
    const parsed = parseForecastResults(valid);
    expect(parsed.models.map((m) => m.id)).toEqual(["persistence", "seasonal", "gb", "mlp", "chronos"]);
    expect(parsed.sensors[0].actual).toEqual(sensor.actual);
  });

  it.each([
    ["not an object", [], /file must be an object/],
    ["two key numbers", { ...valid, keyNumbers: valid.keyNumbers.slice(0, 2) }, /keyNumbers must have 3 items/],
    ["an empty caveat", { ...valid, keyNumbers: [{ ...valid.keyNumbers[0], caveat: "" }, ...valid.keyNumbers.slice(1)] }, /keyNumbers\[0\]\.caveat/],
    ["a run date that is not ISO", { ...valid, run: { ...valid.run, lastRun: "13 Oct 2026" } }, /run\.lastRun/],
    ["the old four models", { ...valid, models: valid.models.slice(1) }, /models must list each of/],
    ["a misspelt model id", { ...valid, models: [{ ...valid.models[0], id: "naive" }, ...valid.models.slice(1)] }, /models must list each of/],
    ["an MAE row of the wrong length", { ...valid, models: [{ ...valid.models[0], mae: [1, 2] }, ...valid.models.slice(1)] }, /models\[0\]\.mae must have 5 items/],
    ["a forecast that breaks the chart contract", withSensor({ forecasts: { ...sensor.forecasts, gb: sensor.forecasts.gb.slice(1) } }), /sensors\[0\]\.forecasts\.gb must have 9 items/],
    ["a missing window error", withSensor({ windowMae: { ...sensor.windowMae, chronos: undefined } }), /windowMae\.chronos/],
    ["a number stored as text", withSensor({ actual: ["12", ...sensor.actual.slice(1)] }), /actual\[0\] must be a finite number/],
    ["an origin past midnight", withSensor({ originMinutes: 1440 }), /originMinutes/],
    ["no sensors", { ...valid, sensors: [] }, /sensors must have at least one sensor/],
  ])("rejects %s", (_name, input, message) => {
    expect(() => parseForecastResults(input)).toThrow(message);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test --workspace web -- src/content/results/parse-forecast.test.ts`
Expected: FAIL with `Failed to resolve import "./parse-forecast"`.

- [ ] **Step 3: Write the validator**

`apps/web/src/content/results/parse-forecast.ts`:

```ts
import type { ForecastModelId, ForecastResults } from "../types";

// Checks a results file against the ForecastResults shape and the chart contract before the site uses it.
// It throws on the first problem, so a bad file fails the build instead of reaching a page.
const MODEL_IDS: readonly ForecastModelId[] = ["persistence", "seasonal", "gb", "mlp", "chronos"];
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

type Json = Record<string, unknown>;

function fail(path: string, problem: string): never {
  throw new Error(`forecasting-lab results: ${path} ${problem}`);
}

function object(value: unknown, path: string): Json {
  if (typeof value !== "object" || value === null || Array.isArray(value)) fail(path, "must be an object");
  return value as Json;
}

function text(value: unknown, path: string): string {
  if (typeof value !== "string" || value.trim() === "") fail(path, "must be a non-empty string");
  return value;
}

function isoDate(value: unknown, path: string): string {
  if (!ISO_DATE.test(text(value, path))) fail(path, "must be a YYYY-MM-DD date");
  return value as string;
}

function finite(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) fail(path, "must be a finite number");
  return value;
}

function list(value: unknown, path: string, length?: number): unknown[] {
  if (!Array.isArray(value)) fail(path, "must be an array");
  if (length !== undefined && value.length !== length) fail(path, `must have ${length} items, found ${value.length}`);
  return value;
}

function numbers(value: unknown, path: string, length?: number): number[] {
  return list(value, path, length).map((v, i) => finite(v, `${path}[${i}]`));
}

function checkBase(root: Json): void {
  text(root.answer, "answer");
  list(root.keyNumbers, "keyNumbers", 3).forEach((n, i) => {
    const k = object(n, `keyNumbers[${i}]`);
    for (const field of ["value", "label", "caveat"]) text(k[field], `keyNumbers[${i}].${field}`);
  });
  const run = object(root.run, "run");
  for (const field of ["commit", "manifest", "python"]) text(run[field], `run.${field}`);
  isoDate(run.lastRun, "run.lastRun");
  const retrieved = object(root.retrieved, "retrieved");
  if (Object.keys(retrieved).length === 0) fail("retrieved", "must name at least one source");
  for (const [name, date] of Object.entries(retrieved)) isoDate(date, `retrieved.${name}`);
}

function checkModels(root: Json, horizons: number): void {
  const ids = list(root.models, "models").map((m, i) => {
    const model = object(m, `models[${i}]`);
    text(model.name, `models[${i}].name`);
    numbers(model.mae, `models[${i}].mae`, horizons);
    return model.id;
  });
  if (ids.length !== MODEL_IDS.length || MODEL_IDS.some((id) => !ids.includes(id))) fail("models", `must list each of ${MODEL_IDS.join(", ")} once`);
}

function checkSensor(value: unknown, path: string): void {
  const s = object(value, path);
  text(s.id, `${path}.id`);
  text(s.label, `${path}.label`);
  const origin = finite(s.originMinutes, `${path}.originMinutes`);
  if (!Number.isInteger(origin) || origin < 0 || origin >= 24 * 60) fail(`${path}.originMinutes`, "must be a whole minute of the day");
  if (finite(s.stepMinutes, `${path}.stepMinutes`) <= 0) fail(`${path}.stepMinutes`, "must be positive");
  const past = finite(s.pastSteps, `${path}.pastSteps`);
  if (!Number.isInteger(past) || past < 1) fail(`${path}.pastSteps`, "must be a positive whole number");
  const ahead = numbers(s.actual, `${path}.actual`).length - past - 1;
  if (ahead < 1) fail(`${path}.actual`, "must cover the past steps, the origin and at least one step ahead");
  const forecasts = object(s.forecasts, `${path}.forecasts`);
  const windowMae = object(s.windowMae, `${path}.windowMae`);
  for (const id of MODEL_IDS) {
    numbers(forecasts[id], `${path}.forecasts.${id}`, ahead + 1);
    finite(windowMae[id], `${path}.windowMae.${id}`);
  }
}

export function parseForecastResults(json: unknown): ForecastResults {
  const root = object(json, "file");
  checkBase(root);
  const horizons = numbers(root.horizons, "horizons");
  if (horizons.length === 0 || horizons.some((h) => h <= 0)) fail("horizons", "must be positive minutes");
  checkModels(root, horizons.length);
  const sensors = list(root.sensors, "sensors");
  if (sensors.length === 0) fail("sensors", "must have at least one sensor");
  sensors.forEach((s, i) => checkSensor(s, `sensors[${i}]`));
  return root as unknown as ForecastResults;
}
```

- [ ] **Step 4: Run the tests and checks**

Run: `npm test --workspace web -- src/content/results/parse-forecast.test.ts`, then `npm test`, `npm run typecheck` and `npm run lint`.
Expected: `Tests  13 passed (13)` for the file, `Tests  116 passed (116)` overall, and no type or lint errors.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/content/results/parse-forecast.ts apps/web/src/content/results/parse-forecast.test.ts
git commit -m "feat: validate Forecasting Lab results files"
```

---

### Task 3: Python workspace and the UCI 608 loader

**Files:**
- Create: `analysis/pyproject.toml`, `analysis/uv.lock` (generated), `analysis/forecasting/__init__.py` (empty), `analysis/forecasting/data.py`, `analysis/tests/__init__.py` (empty), `analysis/tests/conftest.py`
- Test: `analysis/tests/test_data.py`

**Interfaces:**
- Produces, in `forecasting.data`: constants `SOURCE_NAME = "Dataset 608"`, `SOURCE_TITLE`, `SOURCE_URL`, `SOURCE_PAGE`, `SOURCE_DOI`, `SOURCE_LICENCE`, `MAT_NAME`, `ZIP_NAME`, `RETRIEVED_NAME`, `STEP_MINUTES = 15`, `STEPS_PER_DAY = 96`, `WEEKDAYS = 5`, `WEEKDAY_COLUMNS`, `HOUR_COLUMNS`; frozen dataclasses `Traffic(series, adjacency)`, `Block(start, stop)` with `as_list()`, `Split(train, val, test)`, `RawFiles(zip_path, mat_path, retrieved)`; functions `sha256_of(path) -> str`, `fetch(raw_dir) -> RawFiles`, `load(mat_path) -> Traffic`, `check_calendar(features, steps) -> None`, `weekday_of(step) -> int`, `hour_of(step) -> int`, `make_split(steps) -> Split`.
- Produces, in `tests/conftest.py`: `SENSORS = 4`, `STEPS = 1100`, `ADJACENCY`, `synthetic_series()`, `calendar_cells()`, `write_mat()`, and session fixtures `tiny_mat` (a `.mat` path) and `tiny` (a loaded `Traffic`).

- [ ] **Step 1: Create the workspace**

`analysis/pyproject.toml`:

```toml
[project]
name = "observatory-analysis"
version = "0.1.0"
description = "Offline pipelines that produce the portfolio's published study results."
requires-python = ">=3.12,<3.13"
dependencies = [
  "numpy>=2.1,<3",
  "scipy>=1.14,<2",
  "scikit-learn>=1.6,<2",
]

[dependency-groups]
dev = ["pytest>=8.3"]
chronos = ["chronos-forecasting==2.3.2", "torch>=2.4,<3"]

[tool.uv]
package = false
default-groups = ["dev"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-q"
filterwarnings = ["ignore::sklearn.exceptions.ConvergenceWarning"]
```

Create the empty files `analysis/forecasting/__init__.py` and `analysis/tests/__init__.py`.

`analysis/tests/conftest.py`:

```python
"""A tiny synthetic stand-in for traffic_dataset.mat: 4 sensors, 1100 steps, the publisher's calendar fields."""

from pathlib import Path

import numpy as np
import pytest
import scipy.io

from forecasting.data import HOUR_COLUMNS, STEPS_PER_DAY, WEEKDAY_COLUMNS, Traffic, hour_of, load, weekday_of

SENSORS = 4
STEPS = 1100
ADJACENCY = np.array([[0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0]], dtype=np.uint8)


def synthetic_series(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(STEPS)
    daily = 0.35 + 0.25 * np.sin(2 * np.pi * (t % STEPS_PER_DAY) / STEPS_PER_DAY - 1.2)
    levels = np.array([0.6, 0.9, 1.0, 1.2])[:, None]
    return np.clip(levels * daily + rng.normal(0, 0.02, (SENSORS, STEPS)), 0, 1)


def calendar_cells(steps: int, sensors: int = SENSORS) -> np.ndarray:
    cells = np.empty((1, steps), dtype=object)
    for t in range(steps):
        cell = np.zeros((sensors, 48))
        cell[:, WEEKDAY_COLUMNS.start + weekday_of(t)] = 1
        cell[:, HOUR_COLUMNS.start + hour_of(t)] = 1
        cells[0, t] = cell
    return cells


def write_mat(path: Path, series: np.ndarray, adjacency: np.ndarray = ADJACENCY, cells: np.ndarray | None = None) -> Path:
    cells = calendar_cells(series.shape[1], series.shape[0]) if cells is None else cells
    scipy.io.savemat(path, {"tra_Y_tr": series, "tra_X_tr": cells, "tra_adj_mat": adjacency})
    return path


@pytest.fixture(scope="session")
def tiny_mat(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return write_mat(tmp_path_factory.mktemp("raw") / "traffic_dataset.mat", synthetic_series())


@pytest.fixture(scope="session")
def tiny(tiny_mat: Path) -> Traffic:
    return load(tiny_mat)
```

Run: `cd analysis && uv sync`
Expected: uv downloads CPython 3.12 if needed, creates `analysis/.venv` and `analysis/uv.lock`, and installs numpy, scipy, scikit-learn and pytest. Then run `uv pip list | grep -i torch`. Expected: no output. Then `git status --short` from the repository root shows `analysis/` as untracked but nothing under `analysis/.venv/` (it is ignored by the root `.venv/` rule).

- [ ] **Step 2: Write the failing test**

`analysis/tests/test_data.py`:

```python
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest

from forecasting import data
from forecasting.data import Block, load, make_split, sha256_of

from .conftest import ADJACENCY, STEPS, calendar_cells, synthetic_series, write_mat


def test_sha256_of_matches_a_known_digest(tmp_path: Path) -> None:
    path = tmp_path / "x.txt"
    path.write_bytes(b"abc")
    assert sha256_of(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_load_reads_series_and_adjacency(tiny: data.Traffic) -> None:
    assert tiny.series.shape == (4, STEPS)
    assert tiny.adjacency.shape == (4, 4)
    assert tiny.series.min() >= 0 and tiny.series.max() <= 1


def test_load_rejects_a_calendar_that_does_not_match_the_steps(tmp_path: Path) -> None:
    cells = calendar_cells(STEPS)
    cells[0, 200] = cells[0, 300]
    with pytest.raises(ValueError, match="step 200"):
        load(write_mat(tmp_path / "bad.mat", synthetic_series(), cells=cells))


def test_load_rejects_a_sensor_with_no_neighbours(tmp_path: Path) -> None:
    lonely = ADJACENCY.copy()
    lonely[0, 1] = lonely[1, 0] = 0
    with pytest.raises(ValueError, match="neighbour"):
        load(write_mat(tmp_path / "lonely.mat", synthetic_series(), adjacency=lonely))


def test_split_is_ordered_contiguous_and_non_overlapping() -> None:
    split = make_split(1261)
    assert split.train == Block(0, 864)
    assert split.val == Block(864, 1056)
    assert split.test == Block(1056, 1261)
    assert split.train.stop == split.val.start and split.val.stop == split.test.start
    assert set(range(*split.train.as_list())).isdisjoint(range(*split.test.as_list()))


def test_split_needs_a_test_block() -> None:
    with pytest.raises(ValueError):
        make_split(1056)


def test_fetch_reuses_the_cache_without_the_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with zipfile.ZipFile(tmp_path / data.ZIP_NAME, "w") as archive:
        archive.writestr(data.MAT_NAME, b"mat bytes")
    (tmp_path / data.RETRIEVED_NAME).write_text(json.dumps({"retrieved": "2026-10-13T01:02:03+00:00"}))

    def no_network(*_: object) -> None:
        raise AssertionError("fetch went to the network")

    monkeypatch.setattr(data.urllib.request, "urlretrieve", no_network)
    raw = data.fetch(tmp_path)
    assert raw.mat_path.read_bytes() == b"mat bytes"
    assert raw.retrieved == "2026-10-13T01:02:03+00:00"


def test_calendar_helpers_follow_the_publisher_fields() -> None:
    assert (data.weekday_of(0), data.hour_of(0)) == (0, 0)
    assert (data.weekday_of(95), data.hour_of(95)) == (0, 23)
    assert (data.weekday_of(96 * 5), data.hour_of(96 * 5 + 4)) == (0, 1)
    assert np.isclose(data.STEP_MINUTES * data.STEPS_PER_DAY, 24 * 60)
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest` (in `analysis/`)
Expected: FAIL with `ModuleNotFoundError: No module named 'forecasting.data'` while importing `conftest.py`.

- [ ] **Step 4: Write the loader**

`analysis/forecasting/data.py`:

```python
"""Download, verify and load UCI dataset 608, and define the chronological split."""

from __future__ import annotations

import hashlib
import json
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import scipy.io

SOURCE_NAME = "Dataset 608"
SOURCE_TITLE = "UCI Machine Learning Repository dataset 608, Traffic Flow Forecasting"
SOURCE_URL = "https://archive.ics.uci.edu/static/public/608/traffic+flow+forecasting.zip"
SOURCE_PAGE = "https://archive.ics.uci.edu/dataset/608/traffic+flow+forecasting"
SOURCE_DOI = "10.24432/C57897"
SOURCE_LICENCE = "CC BY 4.0"  # read from SOURCE_PAGE on 2026-10-13; re-checked in Task 11
MAT_NAME = "traffic_dataset.mat"
ZIP_NAME = "traffic_flow_forecasting.zip"
RETRIEVED_NAME = "retrieved.json"

STEP_MINUTES = 15
STEPS_PER_DAY = 96
WEEKDAYS = 5  # the publisher's calendar has weekdays only
TRAIN_DAYS = 9
VAL_DAYS = 2
WEEKDAY_COLUMNS = slice(10, 15)  # publisher feature layout inside each 36x48 matrix
HOUR_COLUMNS = slice(15, 39)


@dataclass(frozen=True)
class Traffic:
    series: np.ndarray  # (sensors, steps), the publisher's flow scaled to 0 to 1
    adjacency: np.ndarray  # (sensors, sensors), 0 or 1, symmetric, zero diagonal


@dataclass(frozen=True)
class Block:
    start: int
    stop: int  # exclusive

    def as_list(self) -> list[int]:
        return [self.start, self.stop]


@dataclass(frozen=True)
class Split:
    train: Block
    val: Block
    test: Block


@dataclass(frozen=True)
class RawFiles:
    zip_path: Path
    mat_path: Path
    retrieved: str  # ISO 8601 timestamp, UTC


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(raw_dir: Path) -> RawFiles:
    """Download the zip once, record when, and extract the .mat file. Later runs reuse the cache."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / ZIP_NAME
    stamp_path = raw_dir / RETRIEVED_NAME
    if not zip_path.exists() or not stamp_path.exists():
        urllib.request.urlretrieve(SOURCE_URL, zip_path)
        stamp = datetime.now(UTC).replace(microsecond=0).isoformat()
        stamp_path.write_text(json.dumps({"retrieved": stamp}))
    with zipfile.ZipFile(zip_path) as archive:
        archive.extract(MAT_NAME, raw_dir)
    retrieved = json.loads(stamp_path.read_text())["retrieved"]
    return RawFiles(zip_path=zip_path, mat_path=raw_dir / MAT_NAME, retrieved=retrieved)


def _dense(cell: object) -> np.ndarray:
    return cell.toarray() if hasattr(cell, "toarray") else np.asarray(cell)


def check_calendar(features: np.ndarray, steps: int) -> None:
    """Fail unless the publisher's weekday and hour fields match our step-based calendar."""
    for t in range(steps):
        row = _dense(features[0, t])[0]
        weekday = int(np.argmax(row[WEEKDAY_COLUMNS]))
        hour = int(np.argmax(row[HOUR_COLUMNS]))
        if (weekday, hour) != (weekday_of(t), hour_of(t)):
            raise ValueError(f"step {t}: publisher calendar says weekday {weekday} hour {hour}")


def load(mat_path: Path) -> Traffic:
    raw = scipy.io.loadmat(mat_path)
    series = np.asarray(raw["tra_Y_tr"], dtype=np.float64)
    adjacency = np.asarray(raw["tra_adj_mat"], dtype=np.int64)
    sensors, steps = series.shape
    if adjacency.shape != (sensors, sensors):
        raise ValueError(f"adjacency is {adjacency.shape}, expected {(sensors, sensors)}")
    if not np.isfinite(series).all():
        raise ValueError("series has missing or infinite values")
    if not (adjacency == adjacency.T).all() or adjacency.diagonal().any():
        raise ValueError("adjacency must be symmetric with a zero diagonal")
    if (adjacency.sum(axis=1) == 0).any():
        raise ValueError("every sensor needs at least one neighbour")
    check_calendar(raw["tra_X_tr"], steps)
    return Traffic(series=series, adjacency=adjacency)


def weekday_of(step: int) -> int:
    return (step // STEPS_PER_DAY) % WEEKDAYS


def hour_of(step: int) -> int:
    return (step % STEPS_PER_DAY) * STEP_MINUTES // 60


def make_split(steps: int) -> Split:
    train_stop = TRAIN_DAYS * STEPS_PER_DAY
    val_stop = train_stop + VAL_DAYS * STEPS_PER_DAY
    if steps <= val_stop:
        raise ValueError(f"need more than {val_stop} steps, got {steps}")
    return Split(train=Block(0, train_stop), val=Block(train_stop, val_stop), test=Block(val_stop, steps))
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest`
Expected: `8 passed`.

- [ ] **Step 6: Commit**

```bash
git add analysis/pyproject.toml analysis/uv.lock analysis/forecasting analysis/tests
git commit -m "feat: add the analysis workspace and the UCI 608 loader"
```

---

### Task 4: Leakage-safe features

**Files:**
- Create: `analysis/forecasting/features.py`
- Test: `analysis/tests/test_features.py`

**Interfaces:**
- Consumes: `STEPS_PER_DAY`, `WEEKDAYS`, `Traffic` (Task 3); the `tiny` fixture.
- Produces: `LAGS = 10`, `NEIGHBOUR_WINDOW = 4`, `FIRST_ORIGIN = 9`; `feature_names() -> list[str]` (19 names); `neighbour_means(series, adjacency) -> np.ndarray` (sensors, steps); `calendar_features(origins) -> np.ndarray` (origins, 7); `build_features(series, adjacency, origins) -> np.ndarray` with one row per (origin, sensor), origin-major (row `k * sensors + i` is sensor i at `origins[k]`); `targets(series, origins, steps) -> np.ndarray` in the same row order.

- [ ] **Step 1: Write the failing test**

`analysis/tests/test_features.py`:

```python
import numpy as np
import pytest

from forecasting.data import Traffic
from forecasting.features import FIRST_ORIGIN, LAGS, build_features, feature_names, neighbour_means, targets


def test_one_row_per_origin_and_sensor_with_named_columns(tiny: Traffic) -> None:
    origins = np.array([100, 101, 102])
    x = build_features(tiny.series, tiny.adjacency, origins)
    assert x.shape == (3 * 4, len(feature_names()))
    assert len(feature_names()) == 19


def test_lags_read_the_origin_and_earlier(tiny: Traffic) -> None:
    x = build_features(tiny.series, tiny.adjacency, np.array([500]))
    names = feature_names()
    for sensor in range(4):
        assert x[sensor, names.index("lag_0")] == tiny.series[sensor, 500]
        assert x[sensor, names.index(f"lag_{LAGS - 1}")] == tiny.series[sensor, 500 - LAGS + 1]


def test_neighbour_mean_averages_adjacent_sensors(tiny: Traffic) -> None:
    means = neighbour_means(tiny.series, tiny.adjacency)
    assert np.isclose(means[1, 300], (tiny.series[0, 300] + tiny.series[2, 300]) / 2)
    assert np.isclose(means[0, 300], tiny.series[1, 300])


def test_no_feature_uses_values_after_its_origin(tiny: Traffic) -> None:
    origins = np.arange(FIRST_ORIGIN, 700)
    future_changed = tiny.series.copy()
    future_changed[:, 700:] = 99.0
    before = build_features(tiny.series, tiny.adjacency, origins)
    after = build_features(future_changed, tiny.adjacency, origins)
    np.testing.assert_array_equal(before, after)


def test_rejects_origins_without_enough_history(tiny: Traffic) -> None:
    with pytest.raises(ValueError):
        build_features(tiny.series, tiny.adjacency, np.array([FIRST_ORIGIN - 1]))


def test_targets_follow_the_feature_row_order(tiny: Traffic) -> None:
    y = targets(tiny.series, np.array([200, 201]), 4)
    assert y.tolist() == [*tiny.series[:, 204].tolist(), *tiny.series[:, 205].tolist()]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_features.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'forecasting.features'`.

- [ ] **Step 3: Write the features**

`analysis/forecasting/features.py`:

```python
"""Features built from the flow series itself. A row for origin t only reads values at t or earlier."""

from __future__ import annotations

import numpy as np

from .data import STEPS_PER_DAY, WEEKDAYS

LAGS = 10
NEIGHBOUR_WINDOW = 4
FIRST_ORIGIN = max(LAGS, NEIGHBOUR_WINDOW) - 1


def feature_names() -> list[str]:
    lags = [f"lag_{k}" for k in range(LAGS)]
    calendar = ["slot_sin", "slot_cos", *[f"weekday_{d}" for d in range(WEEKDAYS)]]
    return [*lags, "neighbour_now", f"neighbour_mean_{NEIGHBOUR_WINDOW}", *calendar]


def neighbour_means(series: np.ndarray, adjacency: np.ndarray) -> np.ndarray:
    """Mean flow of each sensor's neighbours at every step. Column t uses column t only."""
    weights = adjacency / adjacency.sum(axis=1, keepdims=True)
    return weights @ series


def calendar_features(origins: np.ndarray) -> np.ndarray:
    angle = 2 * np.pi * (origins % STEPS_PER_DAY) / STEPS_PER_DAY
    weekday = np.eye(WEEKDAYS)[(origins // STEPS_PER_DAY) % WEEKDAYS]
    return np.column_stack([np.sin(angle), np.cos(angle), weekday])


def build_features(series: np.ndarray, adjacency: np.ndarray, origins: np.ndarray) -> np.ndarray:
    """One row per (origin, sensor), origin-major, so row k * sensors + i is sensor i at origins[k]."""
    origins = np.asarray(origins, dtype=np.int64)
    if origins.size == 0 or origins.min() < FIRST_ORIGIN or origins.max() >= series.shape[1]:
        raise ValueError(f"origins must lie in [{FIRST_ORIGIN}, {series.shape[1]})")
    sensors = series.shape[0]
    neighbours = neighbour_means(series, adjacency)
    lags = np.stack([series[:, origins - k] for k in range(LAGS)], axis=-1)
    recent = np.stack([neighbours[:, origins - k] for k in range(NEIGHBOUR_WINDOW)], axis=-1).mean(axis=-1)
    calendar = np.broadcast_to(calendar_features(origins), (sensors, origins.size, 2 + WEEKDAYS))
    per_sensor = np.concatenate([lags, neighbours[:, origins, None], recent[..., None], calendar], axis=-1)
    return per_sensor.transpose(1, 0, 2).reshape(origins.size * sensors, -1)


def targets(series: np.ndarray, origins: np.ndarray, steps: int) -> np.ndarray:
    """Flow `steps` ahead of each origin, in the same row order as build_features."""
    return series[:, np.asarray(origins) + steps].T.reshape(-1)
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest`
Expected: `14 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/forecasting/features.py analysis/tests/test_features.py
git commit -m "feat: build leakage-safe traffic features"
```

---

### Task 5: Baselines and tuned scikit-learn models

**Files:**
- Create: `analysis/forecasting/models.py`, `analysis/tests/fakes.py`
- Test: `analysis/tests/test_models.py`

**Interfaces:**
- Consumes: `STEPS_PER_DAY`, `Block`, `Split`, `make_split` (Task 3); `FIRST_ORIGIN`, `build_features`, `targets` (Task 4).
- Produces: `MAX_STEPS = 8`, `HORIZON_STEPS = (1, 2, 4, 6, 8)`, `MODEL_IDS = ("persistence", "seasonal", "gb", "mlp", "chronos")`, `MODEL_NAMES` (id to site name); frozen `Settings(gb_grid, mlp_grid, gb_iterations, mlp_iterations)` and `FULL`; frozen `Tuned(estimator, params, val_mae, candidates)`; `persistence(series, origins)` and `seasonal(series, origins)`, each returning (origins, sensors, MAX_STEPS); `train_origins(split, steps)`; `eval_origins(block)`; `make_estimator(kind, params, settings, seed)`; `tune(kind, series, adjacency, split, steps, settings, seed) -> Tuned`; `tuned_forecasts(kind, series, adjacency, split, origins, settings, seed) -> (np.ndarray (origins, sensors, MAX_STEPS), dict[int, dict])`; `scaler_of(pipeline) -> StandardScaler`. In `tests/fakes.py`: `QUICK: Settings` with tiny grids.

- [ ] **Step 1: Write the failing test**

`analysis/tests/fakes.py`:

```python
"""Test doubles: small model grids that train in seconds."""

from forecasting.models import Settings

QUICK = Settings(
    gb_grid=({"learning_rate": 0.1, "max_leaf_nodes": 7}, {"learning_rate": 0.2, "max_leaf_nodes": 7}),
    mlp_grid=({"hidden_layer_sizes": [8], "alpha": 1e-3},),
    gb_iterations=20,
    mlp_iterations=30,
)
```

`analysis/tests/test_models.py`:

```python
import numpy as np
import pytest

from forecasting.data import Traffic, make_split
from forecasting.features import build_features
from forecasting.models import (
    MAX_STEPS,
    eval_origins,
    persistence,
    scaler_of,
    seasonal,
    train_origins,
    tune,
    tuned_forecasts,
)

from .fakes import QUICK


def test_persistence_repeats_the_latest_reading(tiny: Traffic) -> None:
    out = persistence(tiny.series, np.array([300, 301]))
    assert out.shape == (2, 4, MAX_STEPS)
    assert (out[1, 2, :] == tiny.series[2, 301]).all()


def test_seasonal_reads_one_publisher_day_back(tiny: Traffic) -> None:
    out = seasonal(tiny.series, np.array([300]))
    assert out[0, 3, 0] == tiny.series[3, 301 - 96]
    assert out[0, 3, MAX_STEPS - 1] == tiny.series[3, 300 + MAX_STEPS - 96]


def test_seasonal_refuses_origins_without_a_day_of_history(tiny: Traffic) -> None:
    with pytest.raises(ValueError):
        seasonal(tiny.series, np.array([10]))


def test_training_targets_stay_inside_the_training_block() -> None:
    split = make_split(1100)
    for steps in range(1, MAX_STEPS + 1):
        assert train_origins(split, steps).max() + steps < split.train.stop


def test_evaluation_targets_stay_inside_their_block() -> None:
    split = make_split(1100)
    origins = eval_origins(split.test)
    assert origins.min() + 1 == split.test.start
    assert origins.max() + MAX_STEPS == split.test.stop - 1


def test_mlp_scaler_statistics_come_from_training_rows_only(tiny: Traffic) -> None:
    split = make_split(tiny.series.shape[1])
    tuned = tune("mlp", tiny.series, tiny.adjacency, split, 2, QUICK, seed=42)
    train_x = build_features(tiny.series, tiny.adjacency, train_origins(split, 2))
    np.testing.assert_allclose(scaler_of(tuned.estimator).mean_, train_x.mean(axis=0))
    with_val = build_features(tiny.series, tiny.adjacency, np.arange(9, split.val.stop - 2))
    assert not np.allclose(scaler_of(tuned.estimator).mean_, with_val.mean(axis=0))


def test_tuning_picks_the_lowest_validation_error(tiny: Traffic) -> None:
    tuned = tune("gb", tiny.series, tiny.adjacency, make_split(tiny.series.shape[1]), 1, QUICK, seed=42)
    assert tuned.val_mae == min(c["val_mae"] for c in tuned.candidates)
    assert len(tuned.candidates) == 2


def test_tuned_forecasts_are_reproducible_with_a_seed(tiny: Traffic) -> None:
    split = make_split(tiny.series.shape[1])
    origins = eval_origins(split.test)[:5]
    first, chosen = tuned_forecasts("gb", tiny.series, tiny.adjacency, split, origins, QUICK, seed=7)
    second, _ = tuned_forecasts("gb", tiny.series, tiny.adjacency, split, origins, QUICK, seed=7)
    assert first.shape == (5, 4, MAX_STEPS)
    np.testing.assert_array_equal(first, second)
    assert sorted(chosen) == list(range(1, MAX_STEPS + 1))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_models.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'forecasting.models'` (raised from `tests/fakes.py`).

- [ ] **Step 3: Write the models**

`analysis/forecasting/models.py`:

```python
"""Baselines and the two tuned scikit-learn models. Every model forecasts steps 1 to MAX_STEPS directly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import STEPS_PER_DAY, Block, Split
from .features import FIRST_ORIGIN, build_features, targets

MAX_STEPS = 8
HORIZON_STEPS = (1, 2, 4, 6, 8)
MODEL_IDS = ("persistence", "seasonal", "gb", "mlp", "chronos")
MODEL_NAMES = {
    "persistence": "Persistence",
    "seasonal": "Daily seasonal naive",
    "gb": "Gradient boosting",
    "mlp": "Spatial MLP",
    "chronos": "Chronos, zero-shot",
}


@dataclass(frozen=True)
class Settings:
    gb_grid: tuple[dict[str, Any], ...]
    mlp_grid: tuple[dict[str, Any], ...]
    gb_iterations: int
    mlp_iterations: int


FULL = Settings(
    gb_grid=tuple({"learning_rate": lr, "max_leaf_nodes": leaves} for lr in (0.05, 0.1) for leaves in (15, 31)),
    mlp_grid=tuple({"hidden_layer_sizes": size, "alpha": alpha} for size in ((64,), (128, 64)) for alpha in (1e-4, 1e-3)),
    gb_iterations=300,
    mlp_iterations=200,
)


@dataclass(frozen=True)
class Tuned:
    estimator: Any
    params: dict[str, Any]
    val_mae: float
    candidates: list[dict[str, Any]]


def persistence(series: np.ndarray, origins: np.ndarray) -> np.ndarray:
    """(origins, sensors, MAX_STEPS): the latest reading, repeated."""
    latest = series[:, origins].T
    return np.repeat(latest[:, :, None], MAX_STEPS, axis=2)


def seasonal(series: np.ndarray, origins: np.ndarray) -> np.ndarray:
    """(origins, sensors, MAX_STEPS): the reading one publisher day (96 steps) before each target."""
    lookup = origins[:, None] + np.arange(1, MAX_STEPS + 1)[None, :] - STEPS_PER_DAY
    if lookup.min() < 0:
        raise ValueError("seasonal naive needs a full day of history before the first origin")
    return series[:, lookup].transpose(1, 0, 2)


def train_origins(split: Split, steps: int) -> np.ndarray:
    """Origins whose target `steps` ahead still falls inside the training block."""
    return np.arange(FIRST_ORIGIN, split.train.stop - steps)


def eval_origins(block: Block) -> np.ndarray:
    """Origins whose targets at every step from 1 to MAX_STEPS fall inside the block."""
    origins = np.arange(block.start - 1, block.stop - MAX_STEPS)
    if origins.size == 0:
        raise ValueError(f"block {block} is too short to score {MAX_STEPS} steps ahead")
    return origins


def make_estimator(kind: str, params: dict[str, Any], settings: Settings, seed: int) -> Any:
    if kind == "gb":
        return HistGradientBoostingRegressor(max_iter=settings.gb_iterations, early_stopping=False, random_state=seed, **params)
    if kind == "mlp":
        mlp = MLPRegressor(max_iter=settings.mlp_iterations, early_stopping=False, random_state=seed, **params)
        return make_pipeline(StandardScaler(), mlp)
    raise ValueError(f"unknown model kind {kind}")


def tune(kind: str, series: np.ndarray, adjacency: np.ndarray, split: Split, steps: int, settings: Settings, seed: int) -> Tuned:
    """Fit each grid point on train, score it on validation, keep the best. Validation is never used for fitting."""
    grid = settings.gb_grid if kind == "gb" else settings.mlp_grid
    fit_origins = train_origins(split, steps)
    x_train, y_train = build_features(series, adjacency, fit_origins), targets(series, fit_origins, steps)
    val = eval_origins(split.val)
    x_val, y_val = build_features(series, adjacency, val), targets(series, val, steps)
    fitted = [make_estimator(kind, params, settings, seed).fit(x_train, y_train) for params in grid]
    scores = [float(np.mean(np.abs(estimator.predict(x_val) - y_val))) for estimator in fitted]
    best = int(np.argmin(scores))  # the first minimum wins a tie
    candidates = [{**_jsonable(params), "val_mae": score} for params, score in zip(grid, scores, strict=True)]
    return Tuned(estimator=fitted[best], params=_jsonable(grid[best]), val_mae=scores[best], candidates=candidates)


def tuned_forecasts(
    kind: str, series: np.ndarray, adjacency: np.ndarray, split: Split, origins: np.ndarray, settings: Settings, seed: int
) -> tuple[np.ndarray, dict[int, dict[str, Any]]]:
    """(origins, sensors, MAX_STEPS) predictions from one tuned model per step, plus the chosen settings per step."""
    sensors = series.shape[0]
    x = build_features(series, adjacency, origins)
    columns: list[np.ndarray] = []
    chosen: dict[int, dict[str, Any]] = {}
    for steps in range(1, MAX_STEPS + 1):
        tuned = tune(kind, series, adjacency, split, steps, settings, seed)
        columns.append(tuned.estimator.predict(x).reshape(origins.size, sensors))
        chosen[steps] = {"params": tuned.params, "val_mae": tuned.val_mae, "candidates": tuned.candidates}
    return np.stack(columns, axis=2), chosen


def scaler_of(estimator: Pipeline) -> StandardScaler:
    return estimator.named_steps["standardscaler"]


def _jsonable(params: dict[str, Any]) -> dict[str, Any]:
    return {k: list(v) if isinstance(v, tuple) else v for k, v in params.items()}
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest`
Expected: `22 passed`, in about 10 seconds.

- [ ] **Step 5: Commit**

```bash
git add analysis/forecasting/models.py analysis/tests/fakes.py analysis/tests/test_models.py
git commit -m "feat: add persistence, seasonal and tuned scikit-learn models"
```

---

### Task 6: Chronos zero-shot adapter

**Files:**
- Create: `analysis/forecasting/chronos_adapter.py`
- Modify: `analysis/tests/fakes.py` (add `FakeChronos`)
- Test: `analysis/tests/test_chronos_adapter.py`

**Interfaces:**
- Consumes: nothing from earlier tasks at import time. `load_chronos` needs `uv sync --group chronos`.
- Produces: `CHRONOS_MODEL = "amazon/chronos-t5-small"`, `CHRONOS_REVISION = "a971ba21945c4f1796b17a91fe69214b5f4ad472"`, `CHRONOS_LICENCE`, `CONTEXT_LENGTH = 512`, `NUM_SAMPLES = 20`; `SamplePredictor` protocol, `predictor(context: (batch, length), steps) -> (batch, samples, steps)`; `chronos_forecasts(series, origins, steps, predictor) -> np.ndarray` (origins, sensors, steps), the median path; `load_chronos(seed) -> (SamplePredictor, {"torch": ..., "chronos-forecasting": ...})`. In `tests/fakes.py`: `FakeChronos`, which records each context and returns paths centred on the latest reading.

- [ ] **Step 1: Write the failing test**

Replace `analysis/tests/fakes.py` with:

```python
"""Test doubles: a Chronos stand-in that needs no torch, and small model grids that train in seconds."""

import numpy as np

from forecasting.models import Settings

QUICK = Settings(
    gb_grid=({"learning_rate": 0.1, "max_leaf_nodes": 7}, {"learning_rate": 0.2, "max_leaf_nodes": 7}),
    mlp_grid=({"hidden_layer_sizes": [8], "alpha": 1e-3},),
    gb_iterations=20,
    mlp_iterations=30,
)


class FakeChronos:
    """Sample paths centred on the latest reading."""

    def __init__(self, samples: int = 5) -> None:
        self.samples = samples
        self.contexts: list[np.ndarray] = []

    def __call__(self, context: np.ndarray, steps: int) -> np.ndarray:
        self.contexts.append(context)
        latest = context[:, -1][:, None, None]
        spread = np.linspace(-0.01, 0.01, self.samples)[None, :, None]
        return np.broadcast_to(latest + spread, (context.shape[0], self.samples, steps)).copy()
```

`analysis/tests/test_chronos_adapter.py`:

```python
import numpy as np
import pytest

from forecasting.chronos_adapter import CONTEXT_LENGTH, chronos_forecasts
from forecasting.data import Traffic

from .fakes import FakeChronos


def test_context_ends_at_the_origin_and_respects_the_window(tiny: Traffic) -> None:
    fake = FakeChronos()
    chronos_forecasts(tiny.series, np.array([100, 900]), 8, fake)
    short, long = fake.contexts
    assert short.shape == (4, 101)
    np.testing.assert_array_equal(short[:, -1], tiny.series[:, 100])
    assert long.shape == (4, CONTEXT_LENGTH)
    np.testing.assert_array_equal(long[:, -1], tiny.series[:, 900])


def test_returns_the_median_sample_path(tiny: Traffic) -> None:
    out = chronos_forecasts(tiny.series, np.array([500]), 8, FakeChronos())
    assert out.shape == (1, 4, 8)
    np.testing.assert_allclose(out[0, :, 3], tiny.series[:, 500])


def test_rejects_a_predictor_with_the_wrong_shape(tiny: Traffic) -> None:
    def broken(context: np.ndarray, steps: int) -> np.ndarray:
        return np.zeros((context.shape[0], steps))

    with pytest.raises(ValueError, match="shape"):
        chronos_forecasts(tiny.series, np.array([500]), 8, broken)


def test_importing_the_adapter_does_not_import_torch() -> None:
    import sys

    assert "torch" not in sys.modules
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_chronos_adapter.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'forecasting.chronos_adapter'`.

- [ ] **Step 3: Write the adapter**

`analysis/forecasting/chronos_adapter.py`:

```python
"""Chronos zero-shot forecasts. torch and chronos are imported only inside load_chronos, so tests never need them."""

from __future__ import annotations

from typing import Protocol

import numpy as np

CHRONOS_MODEL = "amazon/chronos-t5-small"
CHRONOS_REVISION = "a971ba21945c4f1796b17a91fe69214b5f4ad472"  # Hugging Face commit, read on 2026-10-13
CHRONOS_LICENCE = "Apache 2.0"
CONTEXT_LENGTH = 512  # chronos-t5 context window
NUM_SAMPLES = 20


class SamplePredictor(Protocol):
    def __call__(self, context: np.ndarray, steps: int) -> np.ndarray:
        """context (batch, length) to sample paths (batch, samples, steps)."""
        ...


def chronos_forecasts(series: np.ndarray, origins: np.ndarray, steps: int, predictor: SamplePredictor) -> np.ndarray:
    """(origins, sensors, steps): the median sample path, given each sensor's history up to and including the origin."""
    sensors = series.shape[0]
    rows: list[np.ndarray] = []
    for origin in origins:
        context = series[:, max(0, origin + 1 - CONTEXT_LENGTH) : origin + 1]
        samples = np.asarray(predictor(context, steps))
        if samples.ndim != 3 or samples.shape[0] != sensors or samples.shape[2] != steps:
            raise ValueError(f"predictor returned shape {samples.shape}, expected ({sensors}, samples, {steps})")
        rows.append(np.median(samples, axis=1))
    return np.stack(rows)


def load_chronos(seed: int) -> tuple[SamplePredictor, dict[str, str]]:
    """The real predictor on CPU, and the package versions to record. Needs `uv sync --group chronos`."""
    try:
        import chronos
        import torch
        from chronos import BaseChronosPipeline
    except ImportError as error:
        raise SystemExit("Chronos is not installed. Run: uv sync --group chronos") from error

    torch.manual_seed(seed)
    pipeline = BaseChronosPipeline.from_pretrained(CHRONOS_MODEL, revision=CHRONOS_REVISION, device_map="cpu", dtype=torch.float32)

    def predict(context: np.ndarray, steps: int) -> np.ndarray:
        with torch.no_grad():
            samples = pipeline.predict(torch.tensor(context, dtype=torch.float32), prediction_length=steps, num_samples=NUM_SAMPLES)
        return samples.numpy()

    return predict, {"torch": torch.__version__, "chronos-forecasting": chronos.__version__}
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest`
Expected: `26 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/forecasting/chronos_adapter.py analysis/tests/fakes.py analysis/tests/test_chronos_adapter.py
git commit -m "feat: add the Chronos zero-shot adapter behind an optional group"
```

---

### Task 7: MAE with block bootstrap intervals

**Files:**
- Create: `analysis/forecasting/evaluate.py`
- Test: `analysis/tests/test_evaluate.py`

**Interfaces:**
- Produces: `BLOCK_ORIGINS = 8`, `RESAMPLES = 2000`, `INTERVAL = (2.5, 97.5)`; frozen `Estimate(point, low, high)`; `origin_errors(predicted, actual) -> np.ndarray` (one mean absolute error per origin over sensors); `block_resamples(origins, seed, block=8, resamples=2000) -> list[np.ndarray]`; `mae(errors, resamples) -> Estimate`; `reduction(model, baseline, resamples) -> Estimate` (percentage MAE reduction, paired).

- [ ] **Step 1: Write the failing test**

`analysis/tests/test_evaluate.py`:

```python
import numpy as np
import pytest

from forecasting.evaluate import block_resamples, mae, origin_errors, reduction


def test_origin_errors_average_over_sensors() -> None:
    predicted = np.array([[1.0, 2.0], [3.0, 3.0]])
    actual = np.array([[2.0, 4.0], [3.0, 1.0]])
    assert origin_errors(predicted, actual).tolist() == [1.5, 1.0]


def test_origin_errors_reject_mismatched_shapes() -> None:
    with pytest.raises(ValueError):
        origin_errors(np.zeros((2, 3)), np.zeros((3, 2)))


def test_block_resamples_are_seeded_and_keep_blocks_whole() -> None:
    first = block_resamples(20, seed=42, block=8, resamples=50)
    second = block_resamples(20, seed=42, block=8, resamples=50)
    assert all((a == b).all() for a, b in zip(first, second, strict=True))
    for idx in first:
        starts = [i for i in idx if i % 8 == 0]
        assert len(starts) == 3  # three blocks per resample: 0 to 7, 8 to 15, 16 to 19


def test_mae_interval_brackets_the_point() -> None:
    errors = np.random.default_rng(0).uniform(0, 1, 100)
    estimate = mae(errors, block_resamples(100, seed=1))
    assert estimate.low <= estimate.point <= estimate.high
    assert estimate.point == pytest.approx(errors.mean())


def test_reduction_is_paired_and_signed() -> None:
    baseline = np.random.default_rng(0).uniform(1, 2, 64)
    resamples = block_resamples(64, seed=3)
    half = reduction(baseline / 2, baseline, resamples)
    assert half.point == pytest.approx(50) and half.low == pytest.approx(50) and half.high == pytest.approx(50)
    worse = reduction(baseline * 1.1, baseline, resamples)
    assert worse.point == pytest.approx(-10)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_evaluate.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'forecasting.evaluate'`.

- [ ] **Step 3: Write the evaluation helpers**

`analysis/forecasting/evaluate.py`:

```python
"""Mean absolute error with block bootstrap intervals over forecast origins."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

BLOCK_ORIGINS = 8  # two hours of consecutive origins per block, so nearby errors stay together
RESAMPLES = 2000
INTERVAL = (2.5, 97.5)


@dataclass(frozen=True)
class Estimate:
    point: float
    low: float
    high: float


def origin_errors(predicted: np.ndarray, actual: np.ndarray) -> np.ndarray:
    """Absolute error averaged over sensors, one value per origin. Both inputs are (origins, sensors)."""
    if predicted.shape != actual.shape:
        raise ValueError(f"shape mismatch {predicted.shape} and {actual.shape}")
    return np.abs(predicted - actual).mean(axis=1)


def block_resamples(origins: int, seed: int, block: int = BLOCK_ORIGINS, resamples: int = RESAMPLES) -> list[np.ndarray]:
    """Index sets for a non-overlapping block bootstrap: cut the origins into consecutive blocks, draw blocks with replacement."""
    blocks = [np.arange(start, min(start + block, origins)) for start in range(0, origins, block)]
    picks = np.random.default_rng(seed).integers(0, len(blocks), size=(resamples, len(blocks)))
    return [np.concatenate([blocks[j] for j in row]) for row in picks]


def mae(errors: np.ndarray, resamples: list[np.ndarray]) -> Estimate:
    draws = np.array([errors[idx].mean() for idx in resamples])
    low, high = np.percentile(draws, INTERVAL)
    return Estimate(point=float(errors.mean()), low=float(low), high=float(high))


def reduction(model: np.ndarray, baseline: np.ndarray, resamples: list[np.ndarray]) -> Estimate:
    """Percentage MAE reduction of `model` against `baseline`, paired: both use the same resampled origins."""
    draws = np.array([100 * (1 - model[idx].mean() / baseline[idx].mean()) for idx in resamples])
    low, high = np.percentile(draws, INTERVAL)
    return Estimate(point=float(100 * (1 - model.mean() / baseline.mean())), low=float(low), high=float(high))
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest`
Expected: `31 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/forecasting/evaluate.py analysis/tests/test_evaluate.py
git commit -m "feat: score MAE with block bootstrap intervals"
```

---

### Task 8: Run and score every model

**Files:**
- Create: `analysis/forecasting/pipeline.py`
- Modify: `analysis/tests/conftest.py` (add the `tiny_run` fixture)
- Test: `analysis/tests/test_pipeline.py`

**Interfaces:**
- Consumes: `SamplePredictor`, `chronos_forecasts` (Task 6); `STEP_MINUTES`, `Split`, `Traffic` (Task 3); `Estimate`, `block_resamples`, `mae`, `origin_errors`, `reduction` (Task 7); `HORIZON_STEPS`, `MAX_STEPS`, `MODEL_IDS`, `Settings`, `eval_origins`, `persistence`, `seasonal`, `tuned_forecasts` (Task 5).
- Produces: frozen `Comparison(model, against, minutes, estimate)`; frozen `RunResult(origins, actual, forecasts, mae, short, long, tuning)`; `actual_ahead(series, origins)`; `run(traffic, split, predictor, settings, seed) -> RunResult`; `compare_short(errors, resamples)`, `compare_long(errors, resamples)`. In `conftest.py`: session fixture `tiny_run`, one run on the synthetic file with `QUICK` and `FakeChronos`, used by Tasks 8, 9 and 10.

- [ ] **Step 1: Write the failing test**

Replace `analysis/tests/conftest.py` with:

```python
"""A tiny synthetic stand-in for traffic_dataset.mat: 4 sensors, 1100 steps, the publisher's calendar fields."""

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
import scipy.io

from forecasting.data import HOUR_COLUMNS, STEPS_PER_DAY, WEEKDAY_COLUMNS, Traffic, hour_of, load, make_split, weekday_of

if TYPE_CHECKING:
    from forecasting.pipeline import RunResult

SENSORS = 4
STEPS = 1100
ADJACENCY = np.array([[0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0]], dtype=np.uint8)


def synthetic_series(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(STEPS)
    daily = 0.35 + 0.25 * np.sin(2 * np.pi * (t % STEPS_PER_DAY) / STEPS_PER_DAY - 1.2)
    levels = np.array([0.6, 0.9, 1.0, 1.2])[:, None]
    return np.clip(levels * daily + rng.normal(0, 0.02, (SENSORS, STEPS)), 0, 1)


def calendar_cells(steps: int, sensors: int = SENSORS) -> np.ndarray:
    cells = np.empty((1, steps), dtype=object)
    for t in range(steps):
        cell = np.zeros((sensors, 48))
        cell[:, WEEKDAY_COLUMNS.start + weekday_of(t)] = 1
        cell[:, HOUR_COLUMNS.start + hour_of(t)] = 1
        cells[0, t] = cell
    return cells


def write_mat(path: Path, series: np.ndarray, adjacency: np.ndarray = ADJACENCY, cells: np.ndarray | None = None) -> Path:
    cells = calendar_cells(series.shape[1], series.shape[0]) if cells is None else cells
    scipy.io.savemat(path, {"tra_Y_tr": series, "tra_X_tr": cells, "tra_adj_mat": adjacency})
    return path


@pytest.fixture(scope="session")
def tiny_mat(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return write_mat(tmp_path_factory.mktemp("raw") / "traffic_dataset.mat", synthetic_series())


@pytest.fixture(scope="session")
def tiny(tiny_mat: Path) -> Traffic:
    return load(tiny_mat)


@pytest.fixture(scope="session")
def tiny_run(tiny: Traffic) -> "RunResult":
    """One full pipeline run on the synthetic file, shared by the pipeline, export and CLI tests."""
    from forecasting.pipeline import run

    from .fakes import QUICK, FakeChronos

    return run(tiny, make_split(tiny.series.shape[1]), FakeChronos(), QUICK, seed=42)
```

`analysis/tests/test_pipeline.py`:

```python
import numpy as np
import pytest

from forecasting.data import Traffic, make_split
from forecasting.models import HORIZON_STEPS, MAX_STEPS, MODEL_IDS, eval_origins
from forecasting.pipeline import RunResult


def test_every_model_forecasts_every_test_origin(tiny: Traffic, tiny_run: RunResult) -> None:
    origins = eval_origins(make_split(tiny.series.shape[1]).test)
    np.testing.assert_array_equal(tiny_run.origins, origins)
    for model in MODEL_IDS:
        assert tiny_run.forecasts[model].shape == (origins.size, 4, MAX_STEPS)
        assert len(tiny_run.mae[model]) == len(HORIZON_STEPS)


def test_actual_values_are_the_test_targets(tiny: Traffic, tiny_run: RunResult) -> None:
    first = int(tiny_run.origins[0])
    np.testing.assert_array_equal(tiny_run.actual[0, :, 0], tiny.series[:, first + 1])
    assert first + 1 == make_split(tiny.series.shape[1]).test.start


def test_comparisons_name_the_right_models(tiny_run: RunResult) -> None:
    assert tiny_run.short.against == "persistence" and tiny_run.short.minutes == 15
    assert tiny_run.short.model != "persistence"
    assert tiny_run.long.model == "chronos" and tiny_run.long.against in ("gb", "mlp") and tiny_run.long.minutes == 120


def test_persistence_error_matches_a_hand_computation(tiny: Traffic, tiny_run: RunResult) -> None:
    o = tiny_run.origins
    expected = np.abs(tiny.series[:, o + 1] - tiny.series[:, o]).mean()
    assert tiny_run.mae["persistence"][0].point == pytest.approx(expected)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_pipeline.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'forecasting.pipeline'`.

- [ ] **Step 3: Write the pipeline**

`analysis/forecasting/pipeline.py`:

```python
"""Runs every model on the test origins and scores them. No file or network access here."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .chronos_adapter import SamplePredictor, chronos_forecasts
from .data import STEP_MINUTES, Split, Traffic
from .evaluate import Estimate, block_resamples, mae, origin_errors, reduction
from .models import HORIZON_STEPS, MAX_STEPS, MODEL_IDS, Settings, eval_origins, persistence, seasonal, tuned_forecasts

TUNED = ("gb", "mlp")


@dataclass(frozen=True)
class Comparison:
    model: str
    against: str
    minutes: int
    estimate: Estimate


@dataclass(frozen=True)
class RunResult:
    origins: np.ndarray  # test origins
    actual: np.ndarray  # (origins, sensors, MAX_STEPS)
    forecasts: dict[str, np.ndarray]  # model id to (origins, sensors, MAX_STEPS)
    mae: dict[str, list[Estimate]]  # model id to one estimate per horizon in HORIZON_STEPS
    short: Comparison  # best challenger against persistence at the first horizon
    long: Comparison  # Chronos against the better tuned model at the last horizon
    tuning: dict[str, dict[int, dict[str, Any]]]


def actual_ahead(series: np.ndarray, origins: np.ndarray) -> np.ndarray:
    return np.stack([series[:, origins + s].T for s in range(1, MAX_STEPS + 1)], axis=2)


def run(traffic: Traffic, split: Split, predictor: SamplePredictor, settings: Settings, seed: int) -> RunResult:
    series, adjacency = traffic.series, traffic.adjacency
    origins = eval_origins(split.test)
    gb, gb_tuning = tuned_forecasts("gb", series, adjacency, split, origins, settings, seed)
    mlp, mlp_tuning = tuned_forecasts("mlp", series, adjacency, split, origins, settings, seed)
    forecasts = {
        "persistence": persistence(series, origins),
        "seasonal": seasonal(series, origins),
        "gb": gb,
        "mlp": mlp,
        "chronos": chronos_forecasts(series, origins, MAX_STEPS, predictor),
    }
    actual = actual_ahead(series, origins)
    resamples = block_resamples(origins.size, seed)
    errors = {m: {s: origin_errors(forecasts[m][:, :, s - 1], actual[:, :, s - 1]) for s in HORIZON_STEPS} for m in MODEL_IDS}
    scores = {m: [mae(errors[m][s], resamples) for s in HORIZON_STEPS] for m in MODEL_IDS}
    return RunResult(
        origins=origins,
        actual=actual,
        forecasts=forecasts,
        mae=scores,
        short=compare_short(errors, resamples),
        long=compare_long(errors, resamples),
        tuning={"gb": gb_tuning, "mlp": mlp_tuning},
    )


def compare_short(errors: dict[str, dict[int, np.ndarray]], resamples: list[np.ndarray]) -> Comparison:
    first = HORIZON_STEPS[0]
    challengers = [m for m in MODEL_IDS if m != "persistence"]
    best = min(challengers, key=lambda m: errors[m][first].mean())
    estimate = reduction(errors[best][first], errors["persistence"][first], resamples)
    return Comparison(model=best, against="persistence", minutes=first * STEP_MINUTES, estimate=estimate)


def compare_long(errors: dict[str, dict[int, np.ndarray]], resamples: list[np.ndarray]) -> Comparison:
    last = HORIZON_STEPS[-1]
    tuned = min(TUNED, key=lambda m: errors[m][last].mean())
    estimate = reduction(errors["chronos"][last], errors[tuned][last], resamples)
    return Comparison(model="chronos", against=tuned, minutes=last * STEP_MINUTES, estimate=estimate)
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest`
Expected: `35 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/forecasting/pipeline.py analysis/tests/conftest.py analysis/tests/test_pipeline.py
git commit -m "feat: run and score every forecasting model on the test origins"
```

---

### Task 9: Export the results file and template its prose

**Files:**
- Create: `analysis/forecasting/export.py`
- Test: `analysis/tests/test_export.py`

**Interfaces:**
- Consumes: `CHRONOS_MODEL` (Task 6); `STEP_MINUTES`, `STEPS_PER_DAY`, `Block` (Task 3); `Estimate` (Task 7); `HORIZON_STEPS`, `MAX_STEPS`, `MODEL_IDS`, `MODEL_NAMES` (Task 5); `Comparison`, `RunResult` (Task 8).
- Produces: `EXPORT_SCALE = 100`, `PAST_STEPS = 36`, `SENSOR_POSITIONS`, `SENTENCE_NAMES`; `answer_text(short, long) -> str`; `key_numbers(short, long, sensors, test_hours) -> list[dict]` (three entries with `value`, `label`, `caveat`); `pick_sensors(series, test) -> list[int]`; `pick_origin(series, sensor, origins) -> int`; `build_results(result, series, test, run, retrieved) -> dict` in the site's `ForecastResults` shape; `scores_json(result) -> dict`; `write_json(path, payload)`.

- [ ] **Step 1: Write the failing test**

`analysis/tests/test_export.py`:

```python
import re

import numpy as np

from forecasting.data import Traffic, make_split
from forecasting.evaluate import Estimate
from forecasting.export import EXPORT_SCALE, PAST_STEPS, answer_text, build_results, key_numbers, pick_sensors
from forecasting.models import MAX_STEPS, MODEL_IDS
from forecasting.pipeline import Comparison, RunResult

RUN = {"commit": "abc1234", "manifest": "analysis/outputs/forecasting-lab-manifest.json", "python": "3.12.9", "lastRun": "2026-10-13"}
RETRIEVED = {"Dataset 608": "2026-10-13", "chronos-t5-small": "2026-10-13"}
DASHES = re.compile("[\u2013\u2014]")  # en and em dashes


def results(tiny: Traffic, run: RunResult) -> dict:
    return build_results(run, tiny.series, make_split(tiny.series.shape[1]).test, RUN, RETRIEVED)


def test_matches_the_site_chart_contract(tiny: Traffic, tiny_run: RunResult) -> None:
    out = results(tiny, tiny_run)
    assert out["horizons"] == [15, 30, 60, 90, 120]
    assert [m["id"] for m in out["models"]] == list(MODEL_IDS)
    assert all(len(m["mae"]) == 5 for m in out["models"])
    assert len(out["sensors"]) == 3
    for sensor in out["sensors"]:
        assert sensor["pastSteps"] == PAST_STEPS and sensor["stepMinutes"] == 15
        assert len(sensor["actual"]) == PAST_STEPS + MAX_STEPS + 1
        assert 0 <= sensor["originMinutes"] < 24 * 60
        for model in MODEL_IDS:
            assert len(sensor["forecasts"][model]) == MAX_STEPS + 1
            assert sensor["forecasts"][model][0] == sensor["actual"][PAST_STEPS]
            assert sensor["windowMae"][model] >= 0


def test_numbers_are_scaled_computed_values(tiny: Traffic, tiny_run: RunResult) -> None:
    out = results(tiny, tiny_run)
    persistence = next(m for m in out["models"] if m["id"] == "persistence")
    assert persistence["mae"][0] == round(tiny_run.mae["persistence"][0].point * EXPORT_SCALE, 2)
    assert out["keyNumbers"][2]["value"] == "4"


def test_three_key_numbers_with_the_required_fields(tiny: Traffic, tiny_run: RunResult) -> None:
    numbers = results(tiny, tiny_run)["keyNumbers"]
    assert len(numbers) == 3
    for n in numbers:
        assert set(n) == {"value", "label", "caveat"} and all(n.values())


def test_prose_follows_the_copy_rules(tiny: Traffic, tiny_run: RunResult) -> None:
    out = results(tiny, tiny_run)
    prose = [out["answer"], *[f'{n["label"]} {n["caveat"]}' for n in out["keyNumbers"]]]
    for text in prose:
        assert not DASHES.search(text) and "\u2192" not in text  # no arrows


def test_templates_say_lower_or_higher_from_the_sign() -> None:
    better = Comparison("gb", "persistence", 15, Estimate(point=21.6, low=15.2, high=27.9))
    worse = Comparison("chronos", "mlp", 120, Estimate(point=-8.4, low=-14.0, high=-2.5))
    assert answer_text(better, worse) == (
        "At 15 minutes, gradient boosting is the strongest challenger, with 22% lower error than persistence (95% interval 15 to 28%). "
        "At 2 hours, Chronos, used with no tuning, has 8% higher error than the spatial MLP, the better tuned model there (95% interval 2 to 14%)."
    )
    numbers = key_numbers(better, worse, 36, 51)
    assert numbers[0] == {
        "value": "22%",
        "label": "lower error than persistence for gradient boosting at 15 minutes.",
        "caveat": "95% interval 15 to 28%, from a block bootstrap over the test window.",
    }
    assert numbers[1]["label"] == "higher error for Chronos, with no tuning, than the spatial MLP at 2 hours."
    assert numbers[2]["label"] == "sensors scored at 5 horizons on the final 51 hours of data."


def test_picks_three_distinct_sensors_from_low_to_high_flow(tiny: Traffic) -> None:
    picked = pick_sensors(tiny.series, make_split(tiny.series.shape[1]).test)
    assert picked == [0, 1, 2]
    wide = np.tile(np.arange(36.0)[:, None], (1, 1300)) / 36
    assert pick_sensors(wide, make_split(1300).test) == [5, 17, 29]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_export.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'forecasting.export'`.

- [ ] **Step 3: Write the exporter**

`analysis/forecasting/export.py`:

```python
"""Turns a run into the site's ForecastResults JSON and a manifest. All prose comes from templates over computed numbers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .chronos_adapter import CHRONOS_MODEL
from .data import STEP_MINUTES, STEPS_PER_DAY, Block
from .evaluate import Estimate
from .models import HORIZON_STEPS, MAX_STEPS, MODEL_IDS, MODEL_NAMES
from .pipeline import Comparison, RunResult

EXPORT_SCALE = 100  # the publisher's 0 to 1 flow, shown as an index from 0 to 100
PAST_STEPS = 36
SENSOR_POSITIONS = (1 / 6, 1 / 2, 5 / 6)  # low, middle and high traffic sensors by mean test flow
SENTENCE_NAMES = {
    "persistence": "persistence",
    "seasonal": "the daily seasonal naive",
    "gb": "gradient boosting",
    "mlp": "the spatial MLP",
    "chronos": "Chronos",
}
LOCAL_CAVEAT = "One highway corridor near Washington DC, so treat the ranking as local."


def whole(value: float) -> str:
    return str(int(round(value)))


def oriented(estimate: Estimate) -> Estimate:
    """A reduction shown as a positive number, with its interval flipped to match when the change is an increase."""
    if estimate.point >= 0:
        return estimate
    return Estimate(point=-estimate.point, low=-estimate.high, high=-estimate.low)


def direction(estimate: Estimate) -> str:
    return "lower" if estimate.point >= 0 else "higher"


def interval(estimate: Estimate) -> str:
    shown = oriented(estimate)
    return f"95% interval {whole(shown.low)} to {whole(shown.high)}%"


def capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def answer_text(short: Comparison, long: Comparison) -> str:
    first = (
        f"At {short.minutes} minutes, {SENTENCE_NAMES[short.model]} is the strongest challenger, with "
        f"{whole(oriented(short.estimate).point)}% {direction(short.estimate)} error than persistence ({interval(short.estimate)})."
    )
    second = (
        f"At {long.minutes // 60} hours, Chronos, used with no tuning, has {whole(oriented(long.estimate).point)}% "
        f"{direction(long.estimate)} error than {SENTENCE_NAMES[long.against]}, the better tuned model there ({interval(long.estimate)})."
    )
    return f"{first} {second}"


def key_numbers(short: Comparison, long: Comparison, sensors: int, test_hours: int) -> list[dict[str, str]]:
    bootstrap = "from a block bootstrap over the test window."
    return [
        {
            "value": f"{whole(oriented(short.estimate).point)}%",
            "label": f"{direction(short.estimate)} error than persistence for {SENTENCE_NAMES[short.model]} at {short.minutes} minutes.",
            "caveat": f"{capital(interval(short.estimate))}, {bootstrap}",
        },
        {
            "value": f"{whole(oriented(long.estimate).point)}%",
            "label": f"{direction(long.estimate)} error for Chronos, with no tuning, than {SENTENCE_NAMES[long.against]} at {long.minutes // 60} hours.",
            "caveat": f"{capital(interval(long.estimate))}, {bootstrap}",
        },
        {
            "value": str(sensors),
            "label": f"sensors scored at {len(HORIZON_STEPS)} horizons on the final {test_hours} hours of data.",
            "caveat": LOCAL_CAVEAT,
        },
    ]


def pick_sensors(series: np.ndarray, test: Block) -> list[int]:
    order = np.argsort(series[:, test.start : test.stop].mean(axis=1), kind="stable")
    return [int(order[int(q * (len(order) - 1))]) for q in SENSOR_POSITIONS]


def pick_origin(series: np.ndarray, sensor: int, origins: np.ndarray) -> int:
    """Index into origins of the window where this sensor's flow changes most over the forecast horizon."""
    usable = origins >= PAST_STEPS
    change = np.abs(series[sensor, origins + MAX_STEPS] - series[sensor, origins])
    return int(np.argmax(np.where(usable, change, -np.inf)))


def scaled(values: np.ndarray) -> list[float]:
    return [round(float(v) * EXPORT_SCALE, 2) for v in values]


def sensor_entry(result: RunResult, series: np.ndarray, sensor: int) -> dict[str, Any]:
    k = pick_origin(series, sensor, result.origins)
    origin = int(result.origins[k])
    start = series[sensor, origin]
    forecasts = {m: scaled(np.concatenate([[start], result.forecasts[m][k, sensor, :]])) for m in MODEL_IDS}
    window = {m: float(np.abs(result.forecasts[m][k, sensor, :] - result.actual[k, sensor, :]).mean()) for m in MODEL_IDS}
    return {
        "id": f"s{sensor + 1}",
        "label": f"Sensor {sensor + 1}",
        "originMinutes": (origin % STEPS_PER_DAY) * STEP_MINUTES,
        "stepMinutes": STEP_MINUTES,
        "pastSteps": PAST_STEPS,
        "actual": scaled(series[sensor, origin - PAST_STEPS : origin + MAX_STEPS + 1]),
        "forecasts": forecasts,
        "windowMae": {m: round(v * EXPORT_SCALE, 2) for m, v in window.items()},
    }


def build_results(result: RunResult, series: np.ndarray, test: Block, run: dict[str, str], retrieved: dict[str, str]) -> dict[str, Any]:
    test_hours = (test.stop - test.start) * STEP_MINUTES // 60
    return {
        "answer": answer_text(result.short, result.long),
        "keyNumbers": key_numbers(result.short, result.long, series.shape[0], test_hours),
        "run": run,
        "retrieved": retrieved,
        "horizons": [s * STEP_MINUTES for s in HORIZON_STEPS],
        "models": [{"id": m, "name": MODEL_NAMES[m], "mae": [round(e.point * EXPORT_SCALE, 2) for e in result.mae[m]]} for m in MODEL_IDS],
        "sensors": [sensor_entry(result, series, i) for i in pick_sensors(series, test)],
    }


def estimate_json(estimate: Estimate, scale: float = 1) -> dict[str, float]:
    return {"point": round(estimate.point * scale, 4), "low": round(estimate.low * scale, 4), "high": round(estimate.high * scale, 4)}


def comparison_json(comparison: Comparison) -> dict[str, Any]:
    return {"model": comparison.model, "against": comparison.against, "minutes": comparison.minutes, "reduction_percent": estimate_json(comparison.estimate)}


def scores_json(result: RunResult) -> dict[str, Any]:
    return {
        "test_origins": [int(result.origins[0]), int(result.origins[-1])],
        "mae_index_points": {
            m: [{"minutes": s * STEP_MINUTES, **estimate_json(e, EXPORT_SCALE)} for s, e in zip(HORIZON_STEPS, result.mae[m], strict=True)]
            for m in MODEL_IDS
        },
        "short": comparison_json(result.short),
        "long": comparison_json(result.long),
        "chronos_model": CHRONOS_MODEL,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest`
Expected: `41 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/forecasting/export.py analysis/tests/test_export.py
git commit -m "feat: export forecasting results with templated prose"
```

---

### Task 10: CLI, manifest and the Python CI job

**Files:**
- Create: `analysis/forecasting/cli.py`
- Modify: `.github/workflows/ci.yml`
- Test: `analysis/tests/test_cli.py`

**Interfaces:**
- Consumes: `data` (Task 3); `CHRONOS_LICENCE`, `CHRONOS_MODEL`, `CHRONOS_REVISION`, `CONTEXT_LENGTH`, `NUM_SAMPLES`, `load_chronos` (Task 6); `BLOCK_ORIGINS`, `INTERVAL`, `RESAMPLES` (Task 7); `EXPORT_SCALE`, `build_results`, `scores_json`, `write_json` (Task 9); `feature_names` (Task 4); `FULL`, `HORIZON_STEPS`, `MAX_STEPS` (Task 5); `RunResult`, `run` (Task 8).
- Produces: `python -m forecasting.cli [--seed 42] [--raw-dir PATH]`, which writes `apps/web/src/content/results/forecasting-lab.json` and `analysis/outputs/forecasting-lab-manifest.json`; `build_manifest(raw, split, result, seed, packages, git) -> dict`; `git_state() -> {"commit", "dirty"}`; constants `RESULTS_PATH`, `MANIFEST_PATH`. Task 11 runs it.

- [ ] **Step 1: Write the failing test**

`analysis/tests/test_cli.py`:

```python
import json
from pathlib import Path

from forecasting.chronos_adapter import CHRONOS_REVISION
from forecasting.cli import build_manifest
from forecasting.data import SOURCE_URL, RawFiles, make_split, sha256_of
from forecasting.pipeline import RunResult


def test_manifest_records_the_provenance_of_a_run(tmp_path: Path, tiny_run: RunResult) -> None:
    (tmp_path / "data.zip").write_bytes(b"zip bytes")
    (tmp_path / "data.mat").write_bytes(b"mat bytes")
    raw = RawFiles(zip_path=tmp_path / "data.zip", mat_path=tmp_path / "data.mat", retrieved="2026-10-13T01:02:03+00:00")
    manifest = build_manifest(raw, make_split(1100), tiny_run, 42, {"python": "3.12.9"}, {"commit": "abc1234", "dirty": False})

    assert manifest["source"]["url"] == SOURCE_URL
    assert manifest["source"]["retrieved"] == "2026-10-13T01:02:03+00:00"
    assert manifest["source"]["zip_sha256"] == sha256_of(tmp_path / "data.zip")
    assert manifest["source"]["mat_sha256"] == sha256_of(tmp_path / "data.mat")
    assert manifest["split"] == {"train": [0, 864], "val": [864, 1056], "test": [1056, 1100]}
    assert manifest["seeds"] == {"models": 42, "bootstrap": 42, "torch": 42}
    assert manifest["chronos"]["revision"] == CHRONOS_REVISION
    assert manifest["packages"] == {"python": "3.12.9"}
    assert manifest["git"] == {"commit": "abc1234", "dirty": False}
    assert manifest["results_file"] == "apps/web/src/content/results/forecasting-lab.json"
    assert sorted(manifest["tuning"]) == ["gb", "mlp"]
    json.dumps(manifest)  # serialisable as written
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_cli.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'forecasting.cli'`.

- [ ] **Step 3: Write the CLI**

`analysis/forecasting/cli.py`:

```python
"""Entry point: python -m forecasting.cli --seed 42 (run from analysis/ after `uv sync --group chronos`)."""

from __future__ import annotations

import argparse
import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from . import data
from .chronos_adapter import CHRONOS_LICENCE, CHRONOS_MODEL, CHRONOS_REVISION, CONTEXT_LENGTH, NUM_SAMPLES, load_chronos
from .evaluate import BLOCK_ORIGINS, INTERVAL, RESAMPLES
from .export import EXPORT_SCALE, build_results, scores_json, write_json
from .features import feature_names
from .models import FULL, HORIZON_STEPS, MAX_STEPS
from .pipeline import RunResult, run

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ANALYSIS_DIR.parent
RESULTS_PATH = REPO_DIR / "apps/web/src/content/results/forecasting-lab.json"
MANIFEST_PATH = ANALYSIS_DIR / "outputs/forecasting-lab-manifest.json"


def git_state() -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=REPO_DIR, capture_output=True, text=True, check=True).stdout.strip()

    return {"commit": git("rev-parse", "--short", "HEAD"), "dirty": bool(git("status", "--porcelain"))}


def build_manifest(
    raw: data.RawFiles, split: data.Split, result: RunResult, seed: int, packages: dict[str, str], git: dict[str, Any]
) -> dict[str, Any]:
    return {
        "study": "forecasting-lab",
        "source": {
            "title": data.SOURCE_TITLE,
            "url": data.SOURCE_URL,
            "page": data.SOURCE_PAGE,
            "doi": data.SOURCE_DOI,
            "licence": data.SOURCE_LICENCE,
            "retrieved": raw.retrieved,
            "zip_sha256": data.sha256_of(raw.zip_path),
            "mat_sha256": data.sha256_of(raw.mat_path),
        },
        "calendar": {
            "step_minutes": data.STEP_MINUTES,
            "steps_per_day": data.STEPS_PER_DAY,
            "weekdays_only": True,
            "note": "Clock times follow the publisher's hour and weekday fields in tra_X_tr, checked at load time.",
        },
        "split": {"train": split.train.as_list(), "val": split.val.as_list(), "test": split.test.as_list()},
        "features": feature_names(),
        "horizon_steps": list(HORIZON_STEPS),
        "forecast_steps": MAX_STEPS,
        "seeds": {"models": seed, "bootstrap": seed, "torch": seed},
        "bootstrap": {
            "method": "non-overlapping block bootstrap over test origins",
            "block_origins": BLOCK_ORIGINS,
            "resamples": RESAMPLES,
            "percentiles": list(INTERVAL),
        },
        "tuning": {kind: {str(steps): chosen for steps, chosen in per_step.items()} for kind, per_step in result.tuning.items()},
        "chronos": {
            "model": CHRONOS_MODEL,
            "revision": CHRONOS_REVISION,
            "licence": CHRONOS_LICENCE,
            "context_length": CONTEXT_LENGTH,
            "num_samples": NUM_SAMPLES,
            "point_forecast": "median of samples",
        },
        "scores": scores_json(result),
        "export_scale": EXPORT_SCALE,
        "packages": packages,
        "git": git,
        "results_file": str(RESULTS_PATH.relative_to(REPO_DIR)),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m forecasting.cli", description="Run the Forecasting Lab and write its results.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--raw-dir", type=Path, default=ANALYSIS_DIR / "data/raw")
    args = parser.parse_args(argv)

    raw = data.fetch(args.raw_dir)
    traffic = data.load(raw.mat_path)
    split = data.make_split(traffic.series.shape[1])
    predictor, chronos_versions = load_chronos(args.seed)
    result = run(traffic, split, predictor, FULL, args.seed)

    today = datetime.now(UTC).date().isoformat()
    git = git_state()
    libraries = {name: version(name) for name in ("numpy", "scipy", "scikit-learn")}
    packages = {"python": platform.python_version(), **libraries, **chronos_versions}
    write_json(MANIFEST_PATH, build_manifest(raw, split, result, args.seed, packages, git))
    manifest_name = str(MANIFEST_PATH.relative_to(REPO_DIR))
    run_info = {"commit": git["commit"], "manifest": manifest_name, "python": packages["python"], "lastRun": today}
    retrieved = {data.SOURCE_NAME: raw.retrieved[:10], "chronos-t5-small": today}
    write_json(RESULTS_PATH, build_results(result, traffic.series, split.test, run_info, retrieved))
    print(f"wrote {RESULTS_PATH.relative_to(REPO_DIR)} and {MANIFEST_PATH.relative_to(REPO_DIR)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and the help text**

Run: `uv run pytest`, then `uv run python -m forecasting.cli --help`.
Expected: `42 passed`, then a usage line starting `usage: python -m forecasting.cli [-h] [--seed SEED] [--raw-dir RAW_DIR]`. Neither needs torch.

- [ ] **Step 5: Add the CI job**

Replace `.github/workflows/ci.yml` with:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  quality:
    name: Lint, typecheck, test, build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Audit production dependencies
        run: npm audit --omit=dev --audit-level=high

      - name: Lint
        run: npm run lint

      - name: Typecheck
        run: npm run typecheck

      - name: Test
        run: npm test

      - name: Build
        run: npm run build

  analysis:
    name: Python analysis tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: analysis
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v10
        with:
          version: "0.11.4"
          python-version: "3.12"
          enable-cache: true
          cache-dependency-glob: analysis/uv.lock

      # The chronos group (PyTorch) is never installed here; tests use a fake Chronos and a synthetic .mat file.
      - name: Install dependencies
        run: uv sync --locked

      - name: Test
        run: uv run pytest
```

Check that the lock is current, as CI will: `uv sync --locked` (in `analysis/`). Expected: exits 0 with no changes.

- [ ] **Step 6: Commit**

```bash
git add analysis/forecasting/cli.py analysis/tests/test_cli.py .github/workflows/ci.yml
git commit -m "feat: add the forecasting CLI, its manifest and a Python CI job"
```

---

### Task 11: The real run

**Files:**
- Create (written by the pipeline): `apps/web/src/content/results/forecasting-lab.json`, `analysis/outputs/forecasting-lab-manifest.json`
- Possibly modify: `analysis/forecasting/data.py` (`SOURCE_LICENCE`, only if Step 1 finds a different licence)

**Interfaces:**
- Consumes: the CLI (Task 10).
- Produces: the committed results file that Task 12 publishes and Task 13 quotes, and the manifest that the results file names in `run.manifest`.

- [ ] **Step 1: Confirm the licence on the UCI page**

Run: `curl -sL "https://archive.ics.uci.edu/dataset/608/traffic+flow+forecasting" | grep -o "Creative Commons Attribution 4.0 International" | head -1`
Expected: `Creative Commons Attribution 4.0 International`. If the page names a different licence, stop: set `SOURCE_LICENCE` in `analysis/forecasting/data.py` to what the page says, and ask Subashanan before going on, because the study record and spec state CC BY 4.0.

- [ ] **Step 2: Start from a clean tree**

Run: `git checkout -- apps/web/next-env.d.ts` (see "Before you start"), then `git status --porcelain`.
Expected: no output. The run records `git rev-parse --short HEAD` and whether the tree was dirty.

- [ ] **Step 3: Install the Chronos group**

Run (in `analysis/`): `uv sync --group chronos`
Expected: installs `chronos-forecasting==2.3.2`, `torch`, `transformers` and their dependencies into `analysis/.venv`.

- [ ] **Step 4: Run the pipeline**

Run (in `analysis/`): `uv run --group chronos python -m forecasting.cli --seed 42`
This takes about 25 minutes on a laptop CPU: about 2 to 3 minutes for tuning and about 7 seconds per test origin for Chronos (198 origins). Run it in the background with a timeout of at least 45 minutes. The first run downloads the 4.4 MB zip into `analysis/data/raw/` and the Chronos weights into the Hugging Face cache (outside the repository). PyTorch may print a `torch.searchsorted` warning; it is harmless.
Expected last line: `wrote apps/web/src/content/results/forecasting-lab.json and analysis/outputs/forecasting-lab-manifest.json`.

- [ ] **Step 5: Check the outputs**

Run (in `analysis/`):

```bash
uv run python -c "
import json
m = json.load(open('outputs/forecasting-lab-manifest.json'))
r = json.load(open('../apps/web/src/content/results/forecasting-lab.json'))
print(m['source']['zip_sha256'], m['source']['mat_sha256'], m['source']['licence'])
print(m['split'], m['git'], m['chronos']['revision'], m['packages'])
print(r['answer']); [print(n) for n in r['keyNumbers']]
print([s['id'] for s in r['sensors']], r['run'])
"
```

Expected:
- `b09ebe53ec44228bfd008d35fb34d12174b5523f7a735d159d9eea326163bc45 45a3f8b443fd48e2d687d3169d95ac68b6bc31999343b1885eadb787d3aaedbc CC BY 4.0`. If either checksum differs, the publisher changed the file: stop and tell Subashanan.
- `{'train': [0, 864], 'val': [864, 1056], 'test': [1056, 1261]}`, `'dirty': False`, revision `a971ba21945c4f1796b17a91fe69214b5f4ad472`, and versions for python 3.12.x, numpy, scipy, scikit-learn, torch and chronos-forecasting 2.3.2.
- An answer and three key numbers in the template shapes of Task 9, with no dashes, and three sensor ids.

Show Subashanan the answer and key numbers now. The wording is approved at PR time, and any change is made in `forecasting/export.py` and the run repeated, never by editing the JSON.

- [ ] **Step 6: Check that the run reproduces**

Run Step 4 again (on the same day, so the dates match), then `git status --short`.
Expected: the two output files are still untracked and unchanged from the first run (compare with `shasum -a 256` before and after). If they differ, find the source of nondeterminism before committing.

- [ ] **Step 7: Return to the CI environment**

Run (in `analysis/`): `uv sync`, then `uv pip list | grep -i torch`, then `uv run pytest`.
Expected: `uv sync` removes the Chronos group, the grep prints nothing, and `42 passed`.

- [ ] **Step 8: Commit**

```bash
git add apps/web/src/content/results/forecasting-lab.json analysis/outputs/forecasting-lab-manifest.json
git commit -m "chore: publish the first Forecasting Lab run"
```

If Step 1 changed `SOURCE_LICENCE`, add `analysis/forecasting/data.py` to this commit and rerun before committing.

---

### Task 12: Web: publish the results and update the study record

**Files:**
- Modify: `apps/web/src/content/results/index.ts`, `apps/web/src/content/studies.ts`, `apps/web/src/components/study/chapters.tsx`, `apps/web/src/lib/study-results.test.ts`
- Test: `apps/web/src/content/results/index.test.ts`

**Interfaces:**
- Consumes: `parseForecastResults` (Task 2); `forecasting-lab.json` (Task 11); `findStudy` (`content/studies.ts`).
- Produces: `published["forecasting-lab"]`, a validated `ForecastResults`. `getStudyResults("forecasting-lab", env)` now returns `{ data, preview: false }` in every environment.

- [ ] **Step 1: Write the failing tests**

`apps/web/src/content/results/index.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { findStudy } from "../studies";
import { published } from "./index";

const DASHES = /[\u2013\u2014]/; // en and em dashes

describe("published results", () => {
  const forecasting = published["forecasting-lab"]!;

  it("publishes the forecasting lab from the validated results file", () => {
    expect(forecasting.models.map((m) => m.id)).toEqual(["persistence", "seasonal", "gb", "mlp", "chronos"]);
    expect(forecasting.horizons).toEqual([15, 30, 60, 90, 120]);
    expect(forecasting.sensors).toHaveLength(3);
  });

  it("dates every source the study lists", () => {
    for (const source of findStudy("forecasting-lab")!.sources) {
      expect(forecasting.retrieved[source.name]).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it("points at the committed manifest and follows the copy rules", () => {
    expect(forecasting.run.manifest).toBe("analysis/outputs/forecasting-lab-manifest.json");
    for (const line of [forecasting.answer, ...forecasting.keyNumbers.flatMap((n) => [n.label, n.caveat])]) {
      expect(line).not.toMatch(DASHES);
    }
  });
});
```

In `apps/web/src/lib/study-results.test.ts`, replace:

```ts
  it("returns nothing in production when no results are published", () => {
    expect(getStudyResults("penang-pulse", "production")).toBeNull();
    expect(getStudyResults("forecasting-lab", "production")).toBeNull();
    expect(getStudyResults("llm-eval-lab", "production")).toBeNull();
  });
```

with:

```ts
  it("returns nothing in production when no results are published", () => {
    expect(getStudyResults("penang-pulse", "production")).toBeNull();
    expect(getStudyResults("llm-eval-lab", "production")).toBeNull();
  });

  it("returns published results in every environment, never flagged as a preview", () => {
    for (const env of ["production", "development", "test", undefined]) {
      const loaded = getStudyResults("forecasting-lab", env);
      expect(loaded?.preview).toBe(false);
      expect(loaded?.data.models).toHaveLength(5);
    }
  });
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/content/results/index.test.ts src/lib/study-results.test.ts`
Expected: FAIL. `index.test.ts` fails with `Cannot read properties of undefined (reading 'models')`, and the new `study-results` test fails with `expected undefined to be false` for production.

- [ ] **Step 3: Publish the validated file**

Replace `apps/web/src/content/results/index.ts`:

```ts
import type { StudyResultsBySlug } from "../types";
import forecastingLab from "./forecasting-lab.json";
import { parseForecastResults } from "./parse-forecast";

// Real results written by the analysis pipelines in analysis/. Each file is validated on import,
// so a malformed file fails the build instead of reaching a page.
export const published: Partial<StudyResultsBySlug> = {
  "forecasting-lab": parseForecastResults(forecastingLab),
};
```

In `apps/web/src/components/study/chapters.tsx`, replace:

```tsx
                <div key={n.value} className="tile-frame num-tile">
```

with:

```tsx
                <div key={n.label} className="tile-frame num-tile">
```

(Two key numbers can share a value such as "12%"; labels are always distinct.)

- [ ] **Step 4: Update the study record**

In `apps/web/src/content/studies.ts`, replace the whole object whose `slug` is `"forecasting-lab"` (from its opening `{` to its closing `},`) with:

```ts
  {
    slug: "forecasting-lab",
    title: "Forecasting Lab",
    question: "Can a pre-trained time-series model beat a tuned baseline on traffic sensors?",
    status: "published",
    plannedAnswer:
      "This study tests whether Chronos, a pre-trained time-series model used without tuning, can beat persistence, a daily seasonal baseline, a tuned gradient boosting model and a spatial neural net on traffic forecasts up to two hours ahead.",
    figurePlan:
      "forecasts for the next two hours on three sensors, each at the test window where its flow changed most, and each model's error by horizon from 15 minutes to 2 hours.",
    data: "UCI dataset 608, Chronos weights from Hugging Face.",
    tile: { motif: "petals", a: "cobalt", b: "mustard", ground: "sky" },
    tint: "sky",
    themeClass: "s-forecast",
    sources: [
      { name: "Dataset 608", publisher: "UCI Machine Learning Repository", used: "Traffic flow every 15 minutes at 36 highway sensors", licence: "CC BY 4.0" },
      { name: "chronos-t5-small", publisher: "Amazon, via Hugging Face", used: "Pre-trained model weights, used without tuning", licence: "Apache 2.0" },
    ],
    method: [
      "Split the 13 weekdays of readings in time order: 9 days to train, the next 2 to tune and the last 2 to test, with scaling fitted on training data only.",
      "Build features from each sensor's last 10 readings, the time of day, the weekday and the mean flow at its neighbouring sensors.",
      "Compare two baselines, the latest reading and the reading at the same time on the previous day, with gradient boosting and a spatial MLP, each tuned on the validation days only.",
      "Run Chronos zero-shot on each sensor's history up to the forecast time, with no tuning.",
      "Score every model on the test days at 15, 30, 60, 90 and 120 minutes, with 95% intervals from a block bootstrap.",
    ],
    limitations: [
      "One dataset from one US highway corridor near Washington DC.",
      "Only 13 weekdays of data, and the published series leaves out weekends.",
      "The test window is about two days, so the intervals are wide.",
      "No weather or holiday features.",
      "MAE hides rare congestion spikes, which matter most to drivers.",
      "Clock times are the dataset's own; its daily peaks suggest they may run several hours behind local time.",
    ],
    reproduce: {
      commands: ["cd analysis", "uv sync --group chronos", "uv run --group chronos python -m forecasting.cli --seed 42", "cd .. && npm run dev"],
      note: "The first run downloads the dataset and the Chronos weights. The tests need neither: uv run pytest.",
    },
    discussNote: "Have a model you think should be on this chart? Suggestions and corrections are welcome.",
  },
```

- [ ] **Step 5: Run every check, and prove a bad file fails the build**

Run: `npm test`, `npm run lint`, `npm run typecheck`, then `npm run build`.
Expected: `Tests  120 passed (120)`, no lint or type errors, and the build lists `/work/forecasting-lab` under `●  (SSG)`.

Then break the file on purpose and build again:

```bash
cp apps/web/src/content/results/forecasting-lab.json /tmp/forecasting-lab.json
node -e "const f='apps/web/src/content/results/forecasting-lab.json';const fs=require('fs');const d=JSON.parse(fs.readFileSync(f));fs.writeFileSync(f,JSON.stringify({...d,models:d.models.slice(1)}))"
npm run build 2>&1 | grep "forecasting-lab results"
cp /tmp/forecasting-lab.json apps/web/src/content/results/forecasting-lab.json
git diff --stat apps/web/src/content/results/forecasting-lab.json
```

Expected: the build fails and the grep prints `Error: forecasting-lab results: models must list each of persistence, seasonal, gb, mlp, chronos once`; after the copy back, `git diff --stat` prints nothing.

- [ ] **Step 6: Restore the generated file**

Run: `git checkout -- apps/web/next-env.d.ts`

- [ ] **Step 7: Check the page against the JSON**

From `apps/web`, run `npx next start --port 3001` in the background, then `curl -s http://localhost:3001/work/forecasting-lab | grep -o "Preview with illustrative data" | head -1`.
Expected: no output (real results are never a preview). Open `http://localhost:3001/work/forecasting-lab` and check that the answer, the three key numbers, the MAE table and the "Retrieved" dates match `forecasting-lab.json` exactly, and that the status pill reads "Published".

- [ ] **Step 8: Screenshot the figure**

With the server still running, from the repository root:

```bash
npx -y playwright@1.59 screenshot --full-page --wait-for-timeout=1500 --viewport-size=1440,900 http://localhost:3001/work/forecasting-lab .context/fl-real-1440.png
npx -y playwright@1.59 screenshot --full-page --wait-for-timeout=1500 --viewport-size=390,844 http://localhost:3001/work/forecasting-lab .context/fl-real-390.png
```

Look at both. Expected: five coloured lines with persistence dashed, hour labels that wrap past midnight correctly (for example `23:00`, `00:00`, `01:00`), no negative tick on the flow axis, and an error axis whose top tick is just above the largest MAE. Stop the server.

- [ ] **Step 9: Commit**

```bash
git add apps/web/src/content/results/index.ts apps/web/src/content/results/index.test.ts apps/web/src/content/studies.ts apps/web/src/components/study/chapters.tsx apps/web/src/lib/study-results.test.ts
git commit -m "feat: publish real Forecasting Lab results"
```

---

### Task 13: Update the CV PDFs

**Files:**
- Create: `analysis/tools/update_cv.py`
- Modify: `apps/web/public/subashanan-nair-cv.pdf`
- Create, not committed: `.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf` and before and after PNG renders in `.context/resume/`
- Test: `analysis/tests/test_update_cv.py`

**Interfaces:**
- Consumes: `apps/web/src/content/results/forecasting-lab.json` (Task 11): `horizons[0]`, `keyNumbers[2].value` and each model's `mae[0]`.
- Produces: `python tools/update_cv.py SOURCE TARGET --png-dir DIR`, plus pure helpers `change(name, percent)`, `forecast_text(results) -> tuple[str, ...]`, `wrap(text, width, limits)`, `choose(candidates, width, limits)`.

- [ ] **Step 1: Write the failing test**

`analysis/tests/test_update_cv.py`:

```python
import pytest

from tools.update_cv import change, choose, forecast_text, wrap

RESULTS = {
    "horizons": [15, 30, 60, 90, 120],
    "keyNumbers": [{}, {}, {"value": "36"}],
    "models": [
        {"id": "persistence", "mae": [2.0]},
        {"id": "seasonal", "mae": [4.0]},
        {"id": "gb", "mae": [1.5]},
        {"id": "mlp", "mae": [1.9]},
        {"id": "chronos", "mae": [2.1]},
    ],
}


def chars(text: str) -> float:
    return float(len(text))


def test_change_names_the_direction() -> None:
    assert change("gradient boosting", 24.6) == "fell 25% with gradient boosting"
    assert change("zero-shot Chronos", -5.2) == "rose 5% with zero-shot Chronos"


def test_forecast_text_uses_only_numbers_from_the_results() -> None:
    full, short = forecast_text(RESULTS)
    assert full == (
        "Leakage safe 15 minute traffic forecasting benchmark across a 36 sensor network. At 15 minutes versus persistence, "
        "MAE fell 25% with gradient boosting, fell 5% with a spatial MLP and rose 5% with zero-shot Chronos."
    )
    assert short.endswith("At 15 minutes, MAE fell 25% with gradient boosting versus persistence.")


def test_wrap_respects_each_line_width_and_the_line_count() -> None:
    assert wrap("aa bb cc dd", chars, [5, 5]) == ["aa bb", "cc dd"]
    assert wrap("aa bb cc dd", chars, [5]) is None


def test_choose_falls_back_to_a_shorter_wording_then_fails() -> None:
    assert choose(("aa bb cc dd ee", "aa bb"), chars, [5, 5]) == ["aa bb"]
    with pytest.raises(SystemExit, match="shorten"):
        choose(("aaaaaa",), chars, [5])
```

- [ ] **Step 2: Run the test to verify it fails**

Run (in `analysis/`): `uv run pytest tests/test_update_cv.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools'`.

- [ ] **Step 3: Write the tool**

`analysis/tools/update_cv.py`:

```python
"""Rewrites the Forecasting Lab and Penang Pulse entries on page 2 of the CV from the published results.

Run from analysis/:
  uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py SOURCE.pdf TARGET.pdf --png-dir DIR
SOURCE and TARGET may be the same file. PyMuPDF is imported inside main(), so the tests need only the standard library.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_DIR = Path(__file__).resolve().parents[2]
RESULTS_PATH = REPO_DIR / "apps/web/src/content/results/forecasting-lab.json"
PAGE = 1  # zero-based: the projects page
RIGHT_EDGE = 562.0  # widest existing body line ends at 561.8
BODY = {"fontname": "helv", "fontsize": 9.5, "color": (0, 0, 0)}  # LiberationSans is metric-compatible with Helvetica
TECH = {"fontname": "heit", "fontsize": 8.5, "color": (0x55 / 255,) * 3}  # Helvetica-Oblique for the grey tech lines
FORECAST_BULLET = "Leakage safe 15 minute traffic forecasting"
PULSE_BULLET = "Reproducible study of how evenly clinics"
PULSE_TECH_OLD = "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js, React Three Fiber"
PULSE_TECH_NEW = "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js"
PULSE_TEXT = (
    "In progress: a reproducible study of how far residents in each Penang district live from the nearest public clinic, "
    "school and transit stop, using PeGIS facility layers, 2020 census population and OpenStreetMap roads. "
    "Method, sources and limitations are published ahead of any results.",
    "In progress: a reproducible study of how far residents in each Penang district live from the nearest public clinic, "
    "school and transit stop. Method, sources and limitations are published ahead of any results.",
)

Width = Callable[[str], float]


@dataclass(frozen=True)
class Line:
    x: float  # where the text starts, after any bullet
    baseline: float
    top: float
    bottom: float


def change(name: str, percent: float) -> str:
    return f"{'fell' if percent >= 0 else 'rose'} {round(abs(percent))}% with {name}"


def forecast_text(results: dict[str, Any]) -> tuple[str, ...]:
    """Candidate wordings, longest first, built only from numbers in the results file."""
    first = {m["id"]: m["mae"][0] for m in results["models"]}
    cut = {k: 100 * (1 - first[k] / first["persistence"]) for k in ("gb", "mlp", "chronos")}
    minutes = results["horizons"][0]
    sensors = results["keyNumbers"][2]["value"]
    head = f"Leakage safe {minutes} minute traffic forecasting benchmark across a {sensors} sensor network."
    full = (
        f"{head} At {minutes} minutes versus persistence, MAE {change('gradient boosting', cut['gb'])}, "
        f"{change('a spatial MLP', cut['mlp'])} and {change('zero-shot Chronos', cut['chronos'])}."
    )
    short = f"{head} At {minutes} minutes, MAE {change('gradient boosting', cut['gb'])} versus persistence."
    return (full, short)


def wrap(text: str, width: Width, limits: list[float]) -> list[str] | None:
    """Greedy word wrap into at most len(limits) lines, line i no wider than limits[i]. None when it does not fit."""
    lines: list[str] = []
    for word in text.split():
        if lines and width(f"{lines[-1]} {word}") <= limits[len(lines) - 1]:
            lines[-1] = f"{lines[-1]} {word}"
        elif len(lines) < len(limits) and width(word) <= limits[len(lines)]:
            lines.append(word)
        else:
            return None
    return lines


def choose(candidates: tuple[str, ...], width: Width, limits: list[float]) -> list[str]:
    for text in candidates:
        lines = wrap(text, width, limits)
        if lines is not None:
            return lines
    raise SystemExit(f"No wording fits in {len(limits)} lines; shorten the candidates: {candidates[-1]!r}")


def bullet_lines(page: Any, starts_with: str) -> list[Line]:
    """The bullet line whose text starts with `starts_with`, then its indented continuation lines."""
    lines = [line for block in page.get_text("rawdict")["blocks"] for line in block.get("lines", [])]
    texts = ["".join(c["c"] for span in line["spans"] for c in span["chars"]) for line in lines]
    first = next(i for i, t in enumerate(texts) if t.startswith("•") and t.lstrip("• ").startswith(starts_with))
    found: list[Line] = []
    for line in lines[first:]:
        span = line["spans"][0]
        if found and (span["size"] != lines[first]["spans"][0]["size"] or span["chars"][0]["c"] == "•" or "Bold" in span["font"]):
            break
        chars = [c for s in line["spans"] for c in s["chars"]]
        x = next(c["bbox"][0] for c in chars if c["c"] not in "• ")
        found.append(Line(x=x, baseline=span["origin"][1], top=line["bbox"][1], bottom=line["bbox"][3]))
    return found


def replace_bullet(page: Any, starts_with: str, candidates: tuple[str, ...], fitz: Any) -> None:
    targets = bullet_lines(page, starts_with)
    width = lambda s: fitz.get_text_length(s, fontname=BODY["fontname"], fontsize=BODY["fontsize"])  # noqa: E731
    text = choose(candidates, width, [RIGHT_EDGE - line.x for line in targets])
    for line in targets:
        page.add_redact_annot(fitz.Rect(line.x + 0.2, line.top + 0.5, RIGHT_EDGE + 1, line.bottom - 0.5), fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for line, words in zip(targets, text, strict=False):
        page.insert_text((line.x, line.baseline), words, **BODY)


def replace_tech_line(page: Any, old: str, new: str, fitz: Any) -> None:
    hits = page.search_for(old)
    if len(hits) != 1:
        raise SystemExit(f"Expected one tech line {old!r}, found {len(hits)}")
    span = next(s for b in page.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"] if s["text"] == old)
    page.add_redact_annot(fitz.Rect(span["bbox"]), fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    page.insert_text(span["origin"], new, **TECH)


def render(doc: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc[PAGE].get_pixmap(dpi=110).save(path)


def main(argv: list[str] | None = None) -> None:
    import fitz  # PyMuPDF

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--png-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    results = json.loads(RESULTS_PATH.read_text())
    doc = fitz.open(args.source)
    render(doc, args.png_dir / f"{args.target.stem}-before.png")
    page = doc[PAGE]
    replace_tech_line(page, PULSE_TECH_OLD, PULSE_TECH_NEW, fitz)
    replace_bullet(page, PULSE_BULLET, PULSE_TEXT, fitz)
    replace_bullet(page, FORECAST_BULLET, forecast_text(results), fitz)
    render(doc, args.png_dir / f"{args.target.stem}-after.png")
    args.target.parent.mkdir(parents=True, exist_ok=True)
    scratch = args.target.with_suffix(".tmp.pdf")
    doc.save(scratch, garbage=3, deflate=True)
    doc.close()
    os.replace(scratch, args.target)
    print(f"wrote {args.target}")


if __name__ == "__main__":
    main()
```

Run: `uv run pytest`
Expected: `46 passed`.

- [ ] **Step 4: Inspect the spans before editing**

Run (in `analysis/`):

```bash
uv run --no-project --with pymupdf==1.26.7 python -c "
import fitz, sys
for path in sys.argv[1:]:
    page = fitz.open(path)[1]
    print('==', path)
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                if 130 < s['bbox'][1] < 250:
                    print([round(v, 1) for v in s['bbox']], s['font'], round(s['size'], 1), hex(s['color']), repr(s['text']))
" "../.context/attachments/emjv7j/Subashanan Nair Resume - Data Scientist.pdf" ../apps/web/public/subashanan-nair-cv.pdf
```

Expected, for both files: the Penang Pulse tech line in `LiberationSans-Italic` 8.5 `0x555555` ending in `React Three Fiber`; a three-line Penang bullet starting `'•  Reproducible study of how evenly clinics'` in `LiberationSans` 9.5; and a two-line Forecasting Lab bullet starting `'•  Leakage safe 15 minute traffic forecasting'`. If the layout differs (other fonts, sizes or line counts), stop and report it instead of running Step 5.

- [ ] **Step 5: Update both PDFs**

Run (in `analysis/`):

```bash
uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py \
  "../.context/attachments/emjv7j/Subashanan Nair Resume - Data Scientist.pdf" \
  "../.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf" --png-dir ../.context/resume
uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py \
  ../apps/web/public/subashanan-nair-cv.pdf ../apps/web/public/subashanan-nair-cv.pdf --png-dir ../.context/resume
```

Expected: two `wrote ...` lines. If either prints `No wording fits`, shorten the candidates in `update_cv.py` (the text, never the numbers), rerun the tests, and repeat.

- [ ] **Step 6: Check the result**

Run Step 4's command again on `"../.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf"` and `../apps/web/public/subashanan-nair-cv.pdf`.
Expected: the tech line is `Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js` in `Helvetica-Oblique`; the Penang bullet starts `In progress: a reproducible study` and contains no result figures; the Forecasting Lab bullet's percentages equal `100 * (1 - mae / persistence_mae)` at 15 minutes from the JSON, rounded; no line passes x = 562; and nothing below the Forecasting Lab entry has moved.

Open the `*-before.png` and `*-after.png` renders in `.context/resume/` and compare them side by side: same margins, same baselines, bullets intact, no overlap.

Run: `git check-ignore -v ".context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf"`
Expected: one line naming the ignore rule. If it prints nothing, do not commit anything from `.context/` and add `.context/` to `.git/info/exclude` first.

- [ ] **Step 7: Commit**

```bash
git add analysis/tools/update_cv.py analysis/tests/test_update_cv.py apps/web/public/subashanan-nair-cv.pdf
git commit -m "feat: update the CV from the published forecasting results"
```

---

### Task 14: Final checks and pull request

**Files:** none changed.

**Interfaces:**
- Consumes: everything above.
- Produces: a pull request from `codebase-review-plan` to `main`.

- [ ] **Step 1: Run every check**

Run from the root: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`. Then in `analysis/`: `uv sync --locked` and `uv run pytest`.
Expected: `Tests  120 passed (120)`, no lint or type errors, a successful build, and `46 passed`. Restore `apps/web/next-env.d.ts` afterwards with `git checkout -- apps/web/next-env.d.ts`.

- [ ] **Step 2: Check what the branch adds**

Run: `git diff --stat main...HEAD` and `git diff main...HEAD --name-only | grep -E "data/raw|\.venv|\.env|\.vercel|\.context|\.mat$|\.zip$"`.
Expected: the files from the file map only, and no output from the grep.

- [ ] **Step 3: Open the pull request**

Write the body to `/tmp/fl-pr-body.md` with these sections: **Summary** (the pipeline, the five models, the published results, the CV update); **Results for approval** (paste the `answer` and the three key numbers from `forecasting-lab.json` verbatim, and ask Subashanan to approve the wording); **Decisions** (copy the list in section 15 of the spec); **Data findings** (weekdays only, the 0 to 1 scaling, and the clock caveat, from section 4.2 of the spec); **Test plan** as checkboxes: web tests, lint, typecheck and build; `uv run pytest`; the bad-file build check; the screenshots; the CV before and after renders.

```bash
git push -u origin codebase-review-plan
gh pr create --base main --title "feat: publish real Forecasting Lab results" --body-file /tmp/fl-pr-body.md
```

Expected: `gh` prints the pull request URL. CI runs both jobs, `quality` and `analysis`, and both pass.
