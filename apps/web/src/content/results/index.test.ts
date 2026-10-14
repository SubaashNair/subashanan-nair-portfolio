import { describe, expect, it } from "vitest";

import { findStudy } from "../studies";
import { published } from "./index";

const DASHES = /[–—→←↑↓]/; // en and em dashes and arrows

describe("published results", () => {
  const forecasting = published["forecasting-lab"]!;
  const pulse = published["penang-pulse"]!;

  it("publishes the forecasting lab from the validated results file", () => {
    expect(forecasting.models.map((m) => m.id)).toEqual(["persistence", "seasonal", "gb", "mlp", "chronos"]);
    expect(forecasting.horizons).toEqual([15, 30, 60, 90, 120]);
    expect(forecasting.sensors).toHaveLength(3);
  });

  it("publishes Penang Pulse from the validated results file", () => {
    expect(pulse.districts.map((d) => d.id)).toEqual(["tl", "bd", "spu", "spt", "sps"]);
    expect(pulse.geometry.bridges).toHaveLength(2);
    expect(Number(pulse.keyNumbers[1].value.replace(/,/g, ""))).toBe(pulse.points.length); // every facility counted is drawn
  });

  it.each(["forecasting-lab", "penang-pulse"] as const)("dates every source %s lists", (slug) => {
    for (const source of findStudy(slug)!.sources) {
      expect(published[slug]!.retrieved[source.name]).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it.each(["forecasting-lab", "penang-pulse"] as const)("%s points at its committed manifest and follows the copy rules", (slug) => {
    const data = published[slug]!;
    expect(data.run.manifest).toBe(`analysis/outputs/${slug}-manifest.json`);
    for (const line of [data.answer, ...data.keyNumbers.flatMap((n) => [n.label, n.caveat])]) {
      expect(line).not.toMatch(DASHES);
    }
  });
});
