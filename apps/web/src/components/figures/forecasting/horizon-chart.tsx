"use client";

import { useRef } from "react";

import type { ForecastModel } from "@/content/types";
import { palette } from "@/styles/palette";

import { pathOf, scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { MODEL_STYLE } from "./model-style";

interface HorizonChartProps {
  horizons: readonly number[];
  models: readonly ForecastModel[];
  visible: ReadonlySet<string>;
}

export function HorizonChart({ horizons, models, visible }: HorizonChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(340, Math.max(260, w * 0.42)));
  const pad = { l: 40, r: 18, t: 18, b: 40 };
  const x = (i: number): number => pad.l + 20 + i * ((w - pad.l - pad.r - 40) / (horizons.length - 1));
  const y = scale(0, 18, h - pad.b, pad.t);

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Mean absolute error by forecast horizon for each model">
        {[0, 6, 12, 18].map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={v ? 0.1 : 1} strokeWidth={v ? 1 : 1.5} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {horizons.map((hz, i) => <text key={hz} x={x(i)} y={h - pad.b + 22} textAnchor="middle">{hz} min</text>)}
        {models.filter((m) => visible.has(m.id)).map((m) => (
          <g key={m.id}>
            <path className="model-line" d={pathOf(m.mae.map((v, i) => [x(i), y(v)] as const))} fill="none" stroke={MODEL_STYLE[m.id].colour} strokeWidth={2.75} strokeDasharray={MODEL_STYLE[m.id].dash} />
            {m.mae.map((v, i) => <circle key={i} cx={x(i)} cy={y(v)} r={4.5} fill={MODEL_STYLE[m.id].colour} stroke="#fff" strokeWidth={1.5} />)}
          </g>
        ))}
      </svg>
    </div>
  );
}
