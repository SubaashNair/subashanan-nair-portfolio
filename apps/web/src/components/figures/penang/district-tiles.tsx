"use client";

import { TabList } from "@/components/ui/tab-list";
import type { District } from "@/content/types";
import { palette } from "@/styles/palette";

export const BAND_COLOURS = [palette.jade, palette.mustard, palette.rose] as const;
export const BAND_NAMES = ["Under 1 km", "1 to 3 km", "Over 3 km"] as const;

// A district tile: three bands stacked from the floor up (jade near, mustard middle, rose far).
function BandTile({ district }: { district: District }) {
  const tops = district.bands.reduce<number[]>((acc, p) => [...acc, (acc.at(-1) ?? 94) - p * 0.88], []);
  return (
    <svg viewBox="0 0 100 100" aria-hidden="true">
      <rect width="100" height="100" fill={palette.porcelain} />
      {district.bands.map((p, i) => <rect key={i} x="6" y={tops[i].toFixed(2)} width="88" height={(p * 0.88).toFixed(2)} fill={BAND_COLOURS[i]} />)}
      <path d="M50 20 L80 50 L50 80 L20 50Z" fill="none" stroke={palette.porcelain} strokeWidth="3" opacity=".85" />
      <circle cx="50" cy="50" r="5" fill={palette.porcelain} />
      <rect x="6" y="6" width="88" height="88" fill="none" stroke={palette.ink} strokeWidth="1.5" opacity=".6" />
    </svg>
  );
}

interface DistrictTilesProps {
  districts: readonly District[];
  selected: string;
  onSelect: (id: string) => void;
}

export function DistrictTiles({ districts, selected, onSelect }: DistrictTilesProps) {
  return (
    <TabList
      label="Districts"
      idPrefix="district"
      panelId="district-panel"
      className="district-tiles"
      tabClassName=""
      selected={selected}
      onSelect={onSelect}
      items={districts.map((d) => ({
        id: d.id,
        label: (
          <>
            <span className="tile-wrap"><BandTile district={d} /></span>
            <span className="name">{d.short.startsWith("SP ") ? <><abbr title="Seberang Perai">SP</abbr>{d.short.slice(2)}</> : d.short}</span>
            <span className="stat">{d.bands[2]}% over 3 km</span>
          </>
        ),
      }))}
    />
  );
}
