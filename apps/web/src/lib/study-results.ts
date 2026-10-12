import { fixtures } from "@/content/fixtures";
import { published } from "@/content/results";
import type { StudyResultsBySlug, StudySlug } from "@/content/types";

export interface LoadedResults<S extends StudySlug> {
  data: StudyResultsBySlug[S];
  preview: boolean;
}

/**
 * The only place that decides what a study may show.
 * Published results always win. Illustrative fixtures fill the gap only in development and test, and are flagged as a preview.
 * Any other environment (production, staging, undefined) fails closed: with nothing published the answer is null and pages show their planned state.
 * Pages call this at build time on the server; fixture data reaches the browser only in development.
 */
export function getStudyResults<S extends StudySlug>(slug: S, env: string | undefined = process.env.NODE_ENV): LoadedResults<S> | null {
  const real = published[slug];
  if (real) return { data: real, preview: false };
  if (env !== "development" && env !== "test") return null;
  return { data: fixtures[slug], preview: true };
}
