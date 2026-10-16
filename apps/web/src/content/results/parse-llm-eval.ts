import type { LlmEvalResults, ModelRole } from "../types";
import { checks, type Json } from "./parse-checks";

// Checks a results file against the LlmEvalResults shape before the site uses it.
const TASK_IDS = ["all-tools", "stale-tools", "all-memory"] as const;
const ROLES: readonly ModelRole[] = ["cloud", "baseline"];
const MAX_CALLS = 6;
const MAX_EXAMPLES = 6;
const { fail, object, text, finite, whole, list, base } = checks("llm-eval-lab");

function checkRow(value: unknown, path: string): Json {
  const r = object(value, path);
  text(r.model, `${path}.model`);
  if (!ROLES.includes(r.role as ModelRole)) fail(`${path}.role`, `must be one of ${ROLES.join(", ")}`);
  const [low, score, high] = (["low", "score", "high"] as const).map((k) => whole(r[k], `${path}.${k}`, 0, 100));
  if (low > score || score > high) fail(`${path}.score`, "must lie inside its interval");
  const calls = finite(r.callsPerAnswer, `${path}.callsPerAnswer`);
  if (calls < 0 || calls > MAX_CALLS) fail(`${path}.callsPerAnswer`, `must be from 0 to ${MAX_CALLS}`);
  text(r.callsLabel, `${path}.callsLabel`);
  text(r.latency, `${path}.latency`);
  return r;
}

function checkTask(value: unknown, i: number): void {
  const path = `tasks[${i}]`;
  const t = object(value, path);
  if (t.id !== TASK_IDS[i]) fail(`${path}.id`, `must be ${TASK_IDS[i]}, the fixed view order is ${TASK_IDS.join(", ")}`);
  text(t.label, `${path}.label`);
  text(t.metric, `${path}.metric`);
  const rows = list(t.rows, `${path}.rows`).map((r, j) => checkRow(r, `${path}.rows[${j}]`));
  const baselines = rows.filter((r) => r.role === "baseline").length;
  const wanted = t.id === "all-memory" ? 0 : 1;
  if (baselines !== wanted) fail(`${path}.rows`, `must have ${wanted} baseline row${wanted === 1 ? "" : "s"}, found ${baselines}`);
  if (rows.length === baselines) fail(`${path}.rows`, "must have at least one cloud model");
  if (new Set(rows.map((r) => r.model)).size !== rows.length) fail(`${path}.rows`, "must name each model once");
}

function checkExample(value: unknown, i: number): void {
  const path = `errorExamples[${i}]`;
  const e = object(value, path);
  for (const field of ["input", "expected", "model", "output", "note"]) text(e[field], `${path}.${field}`);
  if (typeof e.correct !== "boolean") fail(`${path}.correct`, "must be true or false");
}

export function parseLlmEvalResults(json: unknown): LlmEvalResults {
  const root = object(json, "file");
  base(root);
  list(root.tasks, "tasks", TASK_IDS.length).forEach(checkTask);
  const examples = list(root.errorExamples, "errorExamples");
  if (examples.length > MAX_EXAMPLES) fail("errorExamples", `must have at most ${MAX_EXAMPLES} items`);
  examples.forEach(checkExample);
  return root as unknown as LlmEvalResults;
}
