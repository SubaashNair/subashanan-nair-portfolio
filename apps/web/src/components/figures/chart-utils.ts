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
