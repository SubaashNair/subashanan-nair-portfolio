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
