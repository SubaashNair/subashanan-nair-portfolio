import type { ModelRole } from "@/content/types";
import { palette } from "@/styles/palette";

// Marks use the deep glaze (at least 3:1); interval bands use the light tint.
export const ROLE_COLOUR: Readonly<Record<ModelRole, string>> = { frontier: palette.cobalt, ft: palette.jadeDeep, open: palette.mustardDeep, base: palette.roseDeep };
export const ROLE_TINT: Readonly<Record<ModelRole, string>> = { frontier: palette.cobalt, ft: palette.jade, open: palette.mustard, base: palette.rose };
