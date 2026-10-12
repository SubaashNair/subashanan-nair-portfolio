import { describe, expect, it } from "vitest";

import { experimentUrl, experiments, listedExperiments } from "./experiments";
import { fixtures } from "./fixtures";
import { profile } from "./profile";
import { findStudy, neighbours, studies } from "./studies";

const ISO = /^\d{4}-\d{2}-\d{2}$/;
const DIGIT = /\d/;

describe("study records", () => {
  it("has four unique slugs in a fixed order", () => {
    expect(studies.map((s) => s.slug)).toEqual(["penang-pulse", "forecasting-lab", "llm-eval-lab", "penang-ai-assistant"]);
  });

  it.each(studies.map((s) => [s.slug, s] as const))("%s meets the provenance minimums", (_slug, study) => {
    expect(study.sources.length).toBeGreaterThanOrEqual(1);
    expect(study.method.length).toBeGreaterThanOrEqual(4);
    expect(study.method.length).toBeLessThanOrEqual(5);
    expect(study.limitations.length).toBeGreaterThanOrEqual(3);
  });

  it.each(studies.map((s) => [s.slug, s] as const))("%s planned copy has no numbers except model sizes", (_slug, study) => {
    expect(DIGIT.test(study.plannedAnswer.replace(/\b\d+B\b/g, ""))).toBe(false);
  });

  it("finds studies and wraps previous and next", () => {
    expect(findStudy("nope")).toBeUndefined();
    expect(neighbours("penang-pulse").prev.slug).toBe("penang-ai-assistant");
    expect(neighbours("penang-ai-assistant").next.slug).toBe("penang-pulse");
  });
});

describe("fixtures", () => {
  it.each(Object.entries(fixtures))("%s dates its run and its sources", (slug, data) => {
    expect(data.run.lastRun).toMatch(ISO);
    for (const source of findStudy(slug)?.sources ?? []) {
      expect(data.retrieved[source.name]).toMatch(ISO);
    }
  });

  it("gives every forecast series the right length", () => {
    const f = fixtures["forecasting-lab"]!;
    for (const s of f.sensors) {
      expect(s.actual.length).toBe(s.pastSteps + 25);
      for (const m of f.models) expect(s.forecasts[m.id].length).toBe(25);
    }
  });

  it("keeps the seasonal baseline worst in every sensor window", () => {
    for (const s of fixtures["forecasting-lab"]!.sensors) {
      const others = (["gb", "gru", "chronos"] as const).map((id) => s.windowMae[id]);
      expect(s.windowMae.naive).toBeGreaterThan(Math.max(...others));
    }
  });
});

describe("experiments and profile", () => {
  it("lists 12 tools, each with a description, and a GitHub link for public ones", () => {
    expect(experiments).toHaveLength(12);
    for (const e of experiments) {
      expect(e.description.length).toBeGreaterThan(0);
      if (!e.private) expect(experimentUrl(e.name)).toBe(`https://github.com/SubaashNair/${e.name}`);
    }
  });

  it("marks the three private repositories", () => {
    expect(experiments.filter((e) => e.private).map((e) => e.name).sort()).toEqual(["CU5_project_dashboard", "Land-subsidence-Prediction", "matomari"]);
  });

  it("excludes experiments without a description from the listed set", () => {
    expect(listedExperiments.every((e) => e.description.trim().length > 0)).toBe(true);
    expect(listedExperiments).toHaveLength(12);
  });

  it("uses the chosen brand name", () => {
    expect(profile.name).toBe("Subashanan Nair");
  });
});
