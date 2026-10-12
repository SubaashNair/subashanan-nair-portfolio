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

export const clock = (minutes: number): string =>
  `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
