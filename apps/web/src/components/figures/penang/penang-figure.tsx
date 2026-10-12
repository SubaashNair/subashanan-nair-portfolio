"use client";

import { useState } from "react";

import { ToggleGroup } from "@/components/ui/toggle-group";
import type { PenangResults } from "@/content/types";
import { palette } from "@/styles/palette";

import { DistrictPanel } from "./district-panel";
import { DistrictTiles } from "./district-tiles";
import { CATEGORY_COLOUR, PenangMap } from "./penang-map";

const CATEGORIES = [
  { id: "clinic", label: "Clinics", shape: "sw" },
  { id: "school", label: "Schools", shape: "sw sq" },
  { id: "transit", label: "Transit stops", shape: "sw dia" },
] as const;

export function PenangFigure({ data }: { data: PenangResults }) {
  const [visible, setVisible] = useState<ReadonlySet<string>>(new Set(CATEGORIES.map((c) => c.id)));
  const [selected, setSelected] = useState(data.districts.at(-1)?.id ?? "");
  const district = data.districts.find((d) => d.id === selected) ?? data.districts[0];

  return (
    <div>
      <h3 className="sub">Distance to the nearest clinic, by district</h3>
      <p className="intro">Each tile is a district. Its bands fill from the floor up: jade for residents under 1 km from a public clinic, mustard for 1 to 3 km, rose for over 3 km. Pick a tile to see its numbers and find it on the map.</p>
      <div className="figure-grid">
        <figure className="tile-frame map">
          <PenangMap geometry={data.geometry} points={data.points} visible={visible} selected={selected} />
          <ToggleGroup
            label="Show or hide service types"
            pressed={visible}
            onChange={setVisible}
            items={CATEGORIES.map((c) => ({
              id: c.id,
              label: <><span className={c.shape} style={{ background: CATEGORY_COLOUR[c.id], borderColor: c.id === "school" ? palette.roseDeep : CATEGORY_COLOUR[c.id] }} />{c.label}</>,
            }))}
          />
          <figcaption className="figcap">{data.pointsNote}</figcaption>
        </figure>
        <div>
          <DistrictTiles districts={data.districts} selected={selected} onSelect={setSelected} />
          <DistrictPanel district={district} />
          <p className="figcap"><abbr title="Seberang Perai">SP</abbr> is Seberang Perai. Shares are of residents, by road distance from population-weighted mukim centroids.</p>
        </div>
      </div>
    </div>
  );
}
