import type { StudyResultsBySlug } from "../types";
import forecastingLab from "./forecasting-lab.json";
import { parseForecastResults } from "./parse-forecast";

// Real results written by the analysis pipelines in analysis/. Each file is validated on import,
// so a malformed file fails the build instead of reaching a page.
export const published: Partial<StudyResultsBySlug> = {
  "forecasting-lab": parseForecastResults(forecastingLab),
};
