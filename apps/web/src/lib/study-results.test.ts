import { afterEach, describe, expect, it, vi } from "vitest";

import { getStudyResults } from "./study-results";

describe("getStudyResults", () => {
  it("returns nothing in production when no results are published", () => {
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
      const llm = getStudyResults("llm-eval-lab", env);
      expect(llm?.preview).toBe(false);
      expect(llm?.data.tasks).toHaveLength(3);
    }
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.doUnmock("@/content/results");
    vi.resetModules();
  });

  it("fails closed for an unknown or missing environment", () => {
    expect(getStudyResults("penang-ai-assistant", "staging")).toBeNull();
    // An explicit undefined argument falls back to the default, so the missing case is exercised through the real env.
    vi.stubEnv("NODE_ENV", undefined);
    expect(process.env.NODE_ENV).toBeUndefined();
    expect(getStudyResults("penang-ai-assistant")).toBeNull();
  });

  it("returns illustrative fixtures, flagged as a preview, outside production while a study is unpublished", async () => {
    // Every study with a fixture is now published, so the unpublished case is simulated with an empty set of results.
    vi.resetModules();
    vi.doMock("@/content/results", () => ({ published: {} }));
    const { getStudyResults: load } = await import("./study-results");
    expect(load("llm-eval-lab", "development")?.preview).toBe(true);
    expect(load("llm-eval-lab", "test")?.data.tasks).toHaveLength(3);
    expect(load("llm-eval-lab", "production")).toBeNull();
  });

  it("returns nothing for a study with no published result and no fixture, even in development", () => {
    expect(getStudyResults("penang-ai-assistant", "development")).toBeNull();
    expect(getStudyResults("penang-ai-assistant", "test")).toBeNull();
  });
});
