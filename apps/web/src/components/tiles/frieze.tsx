import type { CSSProperties } from "react";

import { friezeUri } from "./tile-geometry";

interface FriezeProps {
  markups: readonly string[];
}

/** Decorative border strip, used only at chapter thresholds. */
export function Frieze({ markups }: FriezeProps) {
  return <div className="frieze" aria-hidden="true" style={{ "--frieze": friezeUri(markups) } as CSSProperties} />;
}
