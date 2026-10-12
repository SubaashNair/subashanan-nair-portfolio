"use client";

import { useRef } from "react";

import type { EvalTask } from "@/content/types";
import { palette } from "@/styles/palette";

import { scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { ROLE_COLOUR } from "./role-style";

const COST_TICKS = [[0.01, "$0.01"], [0.1, "$0.10"], [1, "$1"], [10, "$10"]] as const;

export function CostScoreChart({ task }: { task: EvalTask }) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(380, Math.max(300, w * 0.5)));
  const pad = { l: 44, r: 16, t: 18, b: 32 };
  const lx = scale(Math.log10(0.005), Math.log10(10), pad.l, w - pad.r);
  const x = (v: number): number => lx(Math.log10(v));
  const y = scale(50, 95, h - pad.b, pad.t);

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`${task.metric} against cost per 1k items for each model`}>
        {[50, 60, 70, 80, 90].map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {COST_TICKS.map(([v, label]) => (
          <g key={label}>
            <line x1={x(v)} x2={x(v)} y1={pad.t} y2={h - pad.b} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={x(v)} y={h - pad.b + 20} textAnchor={v === 10 ? "end" : "middle"}>{label}</text>
          </g>
        ))}
        <line x1={pad.l} x2={w - pad.r} y1={h - pad.b} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        {task.rows.map((r) => {
          const px = x(r.costPer1k);
          const py = y(r.score);
          const right = px > w * 0.62;
          return (
            <g key={r.model}>
              <line x1={px} x2={px} y1={y(r.low)} y2={y(r.high)} stroke={ROLE_COLOUR[r.role]} strokeWidth={2.5} strokeLinecap="round" />
              <circle className="score-dot" cx={px} cy={py} r={7.5} fill={ROLE_COLOUR[r.role]} stroke={palette.ink} strokeWidth={2} />
              <text className="strong" x={right ? px + 9 : px + 13} y={right ? py - 15 : py + 4.5} textAnchor={right ? "end" : "start"}>{r.model}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
