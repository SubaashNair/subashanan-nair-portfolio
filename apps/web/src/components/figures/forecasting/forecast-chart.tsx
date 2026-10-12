"use client";

import { useRef } from "react";

import type { ForecastModel, SensorSeries } from "@/content/types";
import { palette } from "@/styles/palette";

import { clock, pathOf, scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { MODEL_STYLE } from "./model-style";

interface ForecastChartProps {
  sensor: SensorSeries;
  models: readonly ForecastModel[];
  visible: ReadonlySet<string>;
}

export function ForecastChart({ sensor, models, visible }: ForecastChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(420, Math.max(300, w * 0.52)));
  const pad = { l: 46, r: 14, t: 34, b: 38 };
  const past = sensor.pastSteps;
  const ahead = sensor.actual.length - past - 1;
  const shown = models.filter((m) => visible.has(m.id));
  const values = [...sensor.actual, ...shown.flatMap((m) => sensor.forecasts[m.id])];
  const lo = Math.floor((Math.min(...values) - 5) / 25) * 25;
  const hi = Math.ceil((Math.max(...values) + 5) / 25) * 25;
  const x = scale(-past, ahead, pad.l, w - pad.r);
  const y = scale(lo, hi, h - pad.b, pad.t);
  const yTicks = Array.from({ length: (hi - lo) / 25 + 1 }, (_, i) => lo + i * 25);
  const hourStep = w < 520 ? 24 : 12;
  const xTicks = Array.from({ length: Math.floor((past + ahead) / hourStep) + 1 }, (_, i) => -past + i * hourStep);

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`Traffic flow for ${sensor.label}, actual and forecast, vehicles per 5 minutes`}>
        <rect x={x(0)} y={pad.t} width={x(ahead) - x(0)} height={h - pad.b - pad.t} fill={palette.sky} />
        <text className="strong" x={x(0) + 8} y={pad.t - 12}>Next 2 hours</text>
        {yTicks.map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {xTicks.map((t) => <text key={t} x={x(t)} y={h - pad.b + 22} textAnchor="middle">{clock(sensor.originMinutes + t * sensor.stepMinutes)}</text>)}
        <line x1={x(0)} x2={x(0)} y1={pad.t} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        <line x1={pad.l} x2={w - pad.r} y1={h - pad.b} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        <path d={pathOf(sensor.actual.map((v, i) => [x(i - past), y(v)] as const))} fill="none" stroke={palette.ink} strokeWidth={2.5} strokeLinejoin="round" />
        {shown.map((m) => (
          <path
            key={m.id}
            className="model-line"
            d={pathOf(sensor.forecasts[m.id].map((v, i) => [x(i), y(v)] as const))}
            fill="none"
            stroke={MODEL_STYLE[m.id].colour}
            strokeWidth={2.75}
            strokeLinejoin="round"
            strokeDasharray={MODEL_STYLE[m.id].dash}
          />
        ))}
      </svg>
    </div>
  );
}
