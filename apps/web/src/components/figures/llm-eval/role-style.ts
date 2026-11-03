import type { ModelRole } from "@/content/types";
import { palette } from "@/styles/palette";

// Marks use the deep glaze (at least 3:1); interval bands use the light tint.
export const ROLE_COLOUR: Readonly<Record<ModelRole, string>> = { cloud: palette.cobalt, baseline: palette.roseDeep };
export const ROLE_TINT: Readonly<Record<ModelRole, string>> = { cloud: palette.cobalt, baseline: palette.rose };
export const ROLE_LABEL: Readonly<Record<ModelRole, string>> = { cloud: "Cloud model", baseline: "Open data baseline" };
