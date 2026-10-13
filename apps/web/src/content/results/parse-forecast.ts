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
