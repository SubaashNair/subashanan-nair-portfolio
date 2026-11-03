"use client";

import { useRef } from "react";

import type { EvalTask } from "@/content/types";
import { palette } from "@/styles/palette";

import { scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { ROLE_COLOUR } from "./role-style";

const MAX_CALLS = 6; // the runner's cap on tool calls per question
const SCORE_TICKS = [0, 20, 40, 60, 80, 100];
const LABEL_GAP = 16; // px between stacked labels

/** Label baselines for points sorted top to bottom, pushed down so no two sit closer than LABEL_GAP. */
export function labelOffsets(ys: readonly number[]): number[] {
  const order = ys.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y);
  const placed = new Array<number>(ys.length);
  let last = -Infinity;
  for (const { y, i } of order) {
    last = Math.max(y, last + LABEL_GAP);
    placed[i] = last;
  }
  return placed;
}

export function CallsScoreChart({ task }: { task: EvalTask }) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(380, Math.max(300, w * 0.5)));
  const pad = { l: 44, r: 16, t: 18, b: 32 };
  const x = scale(0, MAX_CALLS, pad.l + 10, w - pad.r);
  const y = scale(0, 100, h - pad.b, pad.t);
  const labelY = labelOffsets(task.rows.map((r) => y(r.score) + 4.5));

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`${task.metric} against tool calls per answer for each model`}>
        {SCORE_TICKS.map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {Array.from({ length: MAX_CALLS + 1 }, (_, v) => (
          <g key={`x${v}`}>
            <line x1={x(v)} x2={x(v)} y1={pad.t} y2={h - pad.b} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={x(v)} y={h - pad.b + 20} textAnchor="middle">{v}</text>
          </g>
        ))}
        <line x1={pad.l} x2={w - pad.r} y1={h - pad.b} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        {task.rows.map((r, i) => {
          const px = x(Math.min(r.callsPerAnswer, MAX_CALLS));
          const right = px > w * 0.62;
          return (
            <g key={r.model}>
              <line x1={px} x2={px} y1={y(r.low)} y2={y(r.high)} stroke={ROLE_COLOUR[r.role]} strokeWidth={2.5} strokeLinecap="round" />
              <circle className="score-dot" cx={px} cy={y(r.score)} r={7.5} fill={ROLE_COLOUR[r.role]} stroke={palette.ink} strokeWidth={2} />
              <text className="strong" x={right ? px - 13 : px + 13} y={labelY[i]} textAnchor={right ? "end" : "start"}>{r.model}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
