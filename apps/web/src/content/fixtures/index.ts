import type { StudyResultsBySlug } from "../types";
import { forecastFixture } from "./forecasting";
import { llmEvalFixture } from "./llm-eval";
import { penangFixture } from "./penang";

export const fixtures: StudyResultsBySlug = {
  "penang-pulse": penangFixture,
  "forecasting-lab": forecastFixture,
  "llm-eval-lab": llmEvalFixture,
};
