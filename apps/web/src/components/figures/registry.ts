import type { ComponentType } from "react";

import type { StudyResultsBySlug, StudySlug } from "@/content/types";

import { ForecastFigure } from "./forecasting/forecast-figure";
import { LlmEvalFigure } from "./llm-eval/llm-eval-figure";
import { PenangFigure } from "./penang/penang-figure";

export type FigureRegistry = { [S in StudySlug]?: ComponentType<{ data: StudyResultsBySlug[S] }> };

// An unregistered study shows the pending panel.
export const figures: FigureRegistry = {
  "forecasting-lab": ForecastFigure,
  "llm-eval-lab": LlmEvalFigure,
  "penang-pulse": PenangFigure,
};
