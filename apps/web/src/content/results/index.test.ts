import { describe, expect, it } from "vitest";

import { findStudy } from "../studies";
import { published } from "./index";

const DASHES = /[–—]/; // en and em dashes

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
