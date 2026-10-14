// Shared checks for the results validators. Each validator makes its own set, so errors name the study.
// Every check throws on the first problem, so a bad file fails the build instead of reaching a page.
export type Json = Record<string, unknown>;

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export function checks(study: string) {
  const fail = (path: string, problem: string): never => {
    throw new Error(`${study} results: ${path} ${problem}`);
  };

  const object = (value: unknown, path: string): Json => {
    if (typeof value !== "object" || value === null || Array.isArray(value)) return fail(path, "must be an object");
    return value as Json;
  };

  const text = (value: unknown, path: string): string => {
    if (typeof value !== "string" || value.trim() === "") return fail(path, "must be a non-empty string");
    return value;
  };

  const isoDate = (value: unknown, path: string): string => {
    const date = text(value, path);
    return ISO_DATE.test(date) ? date : fail(path, "must be a YYYY-MM-DD date");
  };

  const finite = (value: unknown, path: string): number => {
    if (typeof value !== "number" || !Number.isFinite(value)) return fail(path, "must be a finite number");
    return value;
  };

  const whole = (value: unknown, path: string, min: number, max: number): number => {
    const n = finite(value, path);
    return Number.isInteger(n) && n >= min && n <= max ? n : fail(path, `must be a whole number from ${min} to ${max}`);
  };

  const list = (value: unknown, path: string, length?: number): unknown[] => {
    if (!Array.isArray(value)) return fail(path, "must be an array");
    if (length !== undefined && value.length !== length) return fail(path, `must have ${length} items, found ${value.length}`);
    return value;
  };

  const numbers = (value: unknown, path: string, length?: number): number[] => list(value, path, length).map((v, i) => finite(v, `${path}[${i}]`));

  // The fields every study's results share: answer, key numbers, run and retrieval dates.
  const base = (root: Json): void => {
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
  };

  return { fail, object, text, isoDate, finite, whole, list, numbers, base };
}
