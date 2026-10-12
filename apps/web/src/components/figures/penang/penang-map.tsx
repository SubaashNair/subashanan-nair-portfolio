"use client";

import { useRef, type CSSProperties } from "react";

import type { PenangGeometry, ServiceCategory, ServicePoint } from "@/content/types";
import { palette } from "@/styles/palette";

import { useChartWidth } from "../use-chart-width";

export const CATEGORY_COLOUR: Readonly<Record<ServiceCategory, string>> = { clinic: palette.cobalt, school: palette.roseDeep, transit: palette.peacock };

function Point({ point }: { point: ServicePoint }) {
  const { x, y, category } = point;
  const fill = CATEGORY_COLOUR[category];
  if (category === "clinic") return <circle className="pt" data-cat={category} cx={x} cy={y} r={5.2} fill={fill} stroke="#fff" strokeWidth={1.4} />;
  if (category === "school") return <rect className="pt" data-cat={category} x={x - 4.6} y={y - 4.6} width={9.2} height={9.2} fill={fill} stroke="#fff" strokeWidth={1.4} />;
  return <path className="pt" data-cat={category} d={`M${x} ${y - 6.2}L${x + 6.2} ${y}L${x} ${y + 6.2}L${x - 6.2} ${y}Z`} fill={fill} stroke="#fff" strokeWidth={1.4} />;
}

interface PenangMapProps {
  geometry: PenangGeometry;
  points: readonly ServicePoint[];
  visible: ReadonlySet<string>;
  selected: string;
}

export function PenangMap({ geometry, points, visible, selected }: PenangMapProps) {
  const ref = useRef<HTMLDivElement>(null);
  const width = useChartWidth(ref, 600);
  // Map labels keep a fixed on-screen size however wide the map renders.
  const style = { "--u": (600 / width).toFixed(3) } as CSSProperties;

  return (
    <div ref={ref} style={style}>
      <svg viewBox="0 0 600 500" role="img" aria-labelledby="map-title map-desc">
        <title id="map-title">Public services across Penang</title>
        <desc id="map-desc">Map of Penang Island and Seberang Perai with clinics, schools and transit stops plotted as points. The selected district is shaded.</desc>
        <defs>
          <clipPath id="island-clip"><path d={geometry.island} /></clipPath>
          <clipPath id="mainland-clip"><path d={geometry.mainland} /></clipPath>
        </defs>
        <rect width="600" height="500" fill="#d4e6e4" />
        <path d={geometry.mainland} fill="#fff" />
        <path d={geometry.island} fill="#fff" />
        {geometry.districts.map((d) => (
          <path key={d.id} className={d.id === selected ? "district on" : "district"} data-district={d.id} d={d.d} clipPath={`url(#${d.land}-clip)`} />
        ))}
        <g stroke={palette.inkSoft} strokeWidth={1.5} strokeDasharray="6 5" fill="none">
          {geometry.boundaries.map((b) => <path key={b} d={b} />)}
        </g>
        <path d={geometry.mainland} fill="none" stroke={palette.ink} strokeWidth={1.6} />
        <path d={geometry.island} fill="none" stroke={palette.ink} strokeWidth={1.6} />
        <g stroke={palette.ink} strokeWidth={2.5}>{geometry.bridges.map((b) => <path key={b} d={b} />)}</g>
        <text className="water" x={geometry.water.x} y={geometry.water.y}>{geometry.water.text}</text>
        <g>
          {points.map((p, i) => (
            <g key={i} className={visible.has(p.category) ? undefined : "off"}>
              <Point point={p} />
            </g>
          ))}
        </g>
        {geometry.places.map((p) => <text key={p.text} className="place" x={p.x} y={p.y}>{p.text}</text>)}
      </svg>
    </div>
  );
}
