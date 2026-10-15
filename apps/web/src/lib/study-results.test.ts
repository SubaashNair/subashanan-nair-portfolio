import { afterEach, describe, expect, it, vi } from "vitest";

import { getStudyResults } from "./study-results";

describe("getStudyResults", () => {
  it("returns nothing in production when no results are published", () => {
    expect(getStudyResults("llm-eval-lab", "production")).toBeNull();
    expect(getStudyResults("penang-ai-assistant", "production")).toBeNull();
  });

  it("returns published results in every environment, never flagged as a preview", () => {
    for (const env of ["production", "development", "test", undefined]) {
      const forecasting = getStudyResults("forecasting-lab", env);
      expect(forecasting?.preview).toBe(false);
      expect(forecasting?.data.models).toHaveLength(5);
      const pulse = getStudyResults("penang-pulse", env);
      expect(pulse?.preview).toBe(false);
      expect(pulse?.data.districts).toHaveLength(5);
    }
  });

  afterEach(() => vi.unstubAllEnvs());

  it("fails closed for an unknown or missing environment", () => {
    expect(getStudyResults("llm-eval-lab", "staging")).toBeNull();
    // An explicit undefined argument falls back to the default, so the missing case is exercised through the real env.
    vi.stubEnv("NODE_ENV", undefined);
    expect(process.env.NODE_ENV).toBeUndefined();
    expect(getStudyResults("llm-eval-lab")).toBeNull();
  });

  it("returns illustrative fixtures, flagged as a preview, outside production", () => {
    const loaded = getStudyResults("llm-eval-lab", "development");
    expect(loaded?.preview).toBe(true);
    expect(loaded?.data.tasks).toHaveLength(3);
    expect(getStudyResults("llm-eval-lab", "test")?.preview).toBe(true);
  });

  it("returns nothing for a study with no published result and no fixture, even in development", () => {
    expect(getStudyResults("penang-ai-assistant", "development")).toBeNull();
    expect(getStudyResults("penang-ai-assistant", "test")).toBeNull();
  });
});
