import type { ForecastModelId, ForecastResults } from "../types";
import { checks, type Json } from "./parse-checks";

// Checks a results file against the ForecastResults shape and the chart contract before the site uses it.
const MODEL_IDS: readonly ForecastModelId[] = ["persistence", "seasonal", "gb", "mlp", "chronos"];
const { fail, object, text, finite, list, numbers, base } = checks("forecasting-lab");

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
  base(root);
  const horizons = numbers(root.horizons, "horizons");
  if (horizons.length === 0 || horizons.some((h) => h <= 0)) fail("horizons", "must be positive minutes");
  checkModels(root, horizons.length);
  const sensors = list(root.sensors, "sensors");
  if (sensors.length === 0) fail("sensors", "must have at least one sensor");
  sensors.forEach((s, i) => checkSensor(s, `sensors[${i}]`));
  return root as unknown as ForecastResults;
}
