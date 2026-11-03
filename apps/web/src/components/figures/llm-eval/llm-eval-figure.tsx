"use client";

import { useState } from "react";

import { TabList, tabId } from "@/components/ui/tab-list";
import type { LlmEvalResults, ModelRole } from "@/content/types";
import { palette } from "@/styles/palette";

import { CallsScoreChart } from "./calls-score-chart";
import { ErrorExamples } from "./error-examples";
import { Leaderboard } from "./leaderboard";
import { ROLE_COLOUR, ROLE_LABEL } from "./role-style";

const ROLES: readonly ModelRole[] = ["cloud", "baseline"];

export function LlmEvalFigure({ data }: { data: LlmEvalResults }) {
  const [taskId, setTaskId] = useState(data.tasks[0].id);
  const task = data.tasks.find((t) => t.id === taskId) ?? data.tasks[0];

  return (
    <div>
      <h3 className="sub">Leaderboard</h3>
      <p className="intro">Pick a view. Cloud models and the open data baseline keep their colours across the table and the chart. Bars show the 95% interval on a 0 to 100 scale.</p>
      <TabList label="Views" idPrefix="task" panelId="task-panel" selected={taskId} onSelect={setTaskId} items={data.tasks.map((t) => ({ id: t.id, label: t.label }))} />
      <div className="stack" id="task-panel" role="tabpanel" aria-labelledby={tabId("task", taskId)}>
        <Leaderboard task={task} />
        <figure className="tile-frame">
          <h4 className="panel-title">Tool calls against score</h4>
          <p className="figcap" style={{ margin: "0 0 14px" }}>One point per model for the selected view. Vertical lines are 95% intervals. Up and to the left is a right answer found with fewer lookups.</p>
          <CallsScoreChart task={task} />
          <ul className="band-legend">
            {ROLES.map((role) => <li key={role}><span className="sw" style={{ background: ROLE_COLOUR[role], borderColor: palette.ink }} />{ROLE_LABEL[role]}</li>)}
          </ul>
          <p className="figcap">Share answered with the latest figure on the vertical axis. Mean tool calls per answer on the horizontal axis, capped at 6; the baseline and answers from memory make none.</p>
        </figure>
      </div>
      <ErrorExamples examples={data.errorExamples} />
    </div>
  );
}
