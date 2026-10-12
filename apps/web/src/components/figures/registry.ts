import type { ComponentType } from "react";

import type { StudyResultsBySlug, StudySlug } from "@/content/types";

export type FigureRegistry = { [S in StudySlug]?: ComponentType<{ data: StudyResultsBySlug[S] }> };

// Tasks 7 to 9 register each study's figure here. An unregistered study shows the pending panel.
export const figures: FigureRegistry = {};
