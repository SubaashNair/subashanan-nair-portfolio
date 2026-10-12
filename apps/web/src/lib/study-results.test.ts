import { afterEach, describe, expect, it, vi } from "vitest";

import { getStudyResults } from "./study-results";

describe("getStudyResults", () => {
  it("returns nothing in production when no results are published", () => {
    expect(getStudyResults("penang-pulse", "production")).toBeNull();
    expect(getStudyResults("forecasting-lab", "production")).toBeNull();
    expect(getStudyResults("llm-eval-lab", "production")).toBeNull();
  });

  afterEach(() => vi.unstubAllEnvs());

  it("fails closed for an unknown or missing environment", () => {
    expect(getStudyResults("penang-pulse", "staging")).toBeNull();
    // An explicit undefined argument falls back to the default, so the missing case is exercised through the real env.
    vi.stubEnv("NODE_ENV", undefined);
    expect(process.env.NODE_ENV).toBeUndefined();
    expect(getStudyResults("penang-pulse")).toBeNull();
  });

  it("returns illustrative fixtures, flagged as a preview, outside production", () => {
    const loaded = getStudyResults("llm-eval-lab", "development");
    expect(loaded?.preview).toBe(true);
    expect(loaded?.data.tasks).toHaveLength(3);
    expect(getStudyResults("llm-eval-lab", "test")?.preview).toBe(true);
  });
});
