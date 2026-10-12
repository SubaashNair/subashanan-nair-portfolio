import type { ForecastModelId } from "@/content/types";
import { palette } from "@/styles/palette";

// One colour per model across both charts, the toggles and the table. All are at least 3:1 on porcelain and sky.
export const MODEL_STYLE: Readonly<Record<ForecastModelId, { colour: string; dash?: string }>> = {
  naive: { colour: palette.inkSoft, dash: "7 5" },
  gb: { colour: palette.mustardDeep },
  gru: { colour: palette.cobalt },
  chronos: { colour: palette.jadeDeep },
};
