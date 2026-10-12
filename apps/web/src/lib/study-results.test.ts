import { describe, expect, it } from "vitest";

import { getStudyResults } from "./study-results";

describe("getStudyResults", () => {
  it("returns nothing in production when no results are published", () => {
    expect(getStudyResults("penang-pulse", "production")).toBeNull();
    expect(getStudyResults("forecasting-lab", "production")).toBeNull();
    expect(getStudyResults("llm-eval-lab", "production")).toBeNull();
  });

  it("returns illustrative fixtures, flagged as a preview, outside production", () => {
    const loaded = getStudyResults("llm-eval-lab", "development");
    expect(loaded?.preview).toBe(true);
    expect(loaded?.data.tasks).toHaveLength(3);
  });
});
