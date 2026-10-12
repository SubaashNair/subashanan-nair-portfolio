import type { ComponentType } from "react";

import type { StudyResultsBySlug, StudySlug } from "@/content/types";

import { PenangFigure } from "./penang/penang-figure";

export type FigureRegistry = { [S in StudySlug]?: ComponentType<{ data: StudyResultsBySlug[S] }> };

// An unregistered study shows the pending panel.
export const figures: FigureRegistry = {
  "penang-pulse": PenangFigure,
};
