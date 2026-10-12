import { tabId } from "@/components/ui/tab-list";
import type { District } from "@/content/types";
import { palette } from "@/styles/palette";

import { BAND_COLOURS, BAND_NAMES } from "./district-tiles";

const fmt = (n: number): string => n.toLocaleString("en-GB");

export function DistrictPanel({ district }: { district: District }) {
  const lefts = district.bands.map((_, i) => district.bands.slice(0, i).reduce((a, b) => a + b, 0));
  const far = Math.round((district.population * district.bands[2]) / 100 / 500) * 500;
  return (
    <div className="tile-frame panel" id="district-panel" role="tabpanel" tabIndex={0} aria-labelledby={tabId("district", district.id)}>
      <h4>{district.name}</h4>
      <p className="pop">Population {fmt(district.population)}, share of residents by road distance to the nearest public clinic</p>
      <div className="band-bar" aria-hidden="true">
        {district.bands.map((p, i) => <span key={i} className="band-seg" style={{ left: `${lefts[i]}%`, width: `${p}%`, background: BAND_COLOURS[i] }} />)}
      </div>
      <ul className="band-legend">
        {district.bands.map((p, i) => (
          <li key={i}><span className="sw sq" style={{ background: BAND_COLOURS[i], borderColor: palette.ink }} />{BAND_NAMES[i]}<strong>{p}%</strong></li>
        ))}
      </ul>
      <p className="callout"><strong>About {fmt(far)} residents</strong>live more than 3 km from a public clinic.</p>
    </div>
  );
}
