"use client";

import { useState } from "react";

import { Tile } from "./tile";
import type { TileSpec } from "./tile-geometry";

interface MosaicProps {
  tiles: readonly TileSpec[];
  label: string;
  pair?: boolean;
}

export function Mosaic({ tiles, label, pair = false }: MosaicProps) {
  const [turns, setTurns] = useState<readonly number[]>(() => tiles.map(() => 0));
  const turn = (index: number) => setTurns((prev) => prev.map((n, i) => (i === index ? n + 1 : n)));

  return (
    <div className={pair ? "mosaic pair" : "mosaic"} role="group" aria-label={label}>
      {tiles.map((spec, i) => (
        <button key={i} type="button" aria-label={`Turn tile ${i + 1}`} style={{ transform: `rotate(${turns[i] * 90}deg)` }} onClick={() => turn(i)}>
          <Tile spec={spec} />
        </button>
      ))}
    </div>
  );
}
