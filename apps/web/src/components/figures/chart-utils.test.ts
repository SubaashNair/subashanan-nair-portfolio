import { describe, expect, it } from "vitest";

import { clock, pathOf, scale, seeded } from "./chart-utils";

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
});
