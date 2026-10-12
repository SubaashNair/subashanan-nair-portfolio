import type { CSSProperties } from "react";

import { stepTileUri, thinFriezeUri } from "@/components/tiles/tile-geometry";
import type { StudyRecord } from "@/content/types";

/** CSS variables for a study's thin table frieze and method step tiles. Its other colours come from its theme class. */
export function studyThemeStyle(study: StudyRecord): CSSProperties {
  return {
    "--frieze-thin": thinFriezeUri(study.tile, study.tint),
    "--step-a": stepTileUri(study.tile.a, study.tint),
    "--step-b": stepTileUri(study.tile.b, study.tint),
  } as CSSProperties;
}
