"use client";

import { useState } from "react";

import { TabList, tabId } from "@/components/ui/tab-list";
import type { LlmEvalResults } from "@/content/types";

import { CostScoreChart } from "./cost-score-chart";
import { ErrorExamples } from "./error-examples";
import { Leaderboard } from "./leaderboard";

export function LlmEvalFigure({ data }: { data: LlmEvalResults }) {
  const [taskId, setTaskId] = useState(data.tasks[0].id);
  const task = data.tasks.find((t) => t.id === taskId) ?? data.tasks[0];

  return (
    <div>
      <h3 className="sub">Leaderboard</h3>
      <p className="intro">Pick a task. Each model keeps its colour across the table and the chart. Bars show the 95% interval on a 50 to 100 scale.</p>
      <TabList label="Tasks" idPrefix="task" panelId="task-panel" selected={taskId} onSelect={setTaskId} items={data.tasks.map((t) => ({ id: t.id, label: t.label }))} />
      <div className="stack" id="task-panel" role="tabpanel" aria-labelledby={tabId("task", taskId)}>
        <Leaderboard task={task} />
        <figure className="tile-frame">
          <h4 className="panel-title">Cost against score</h4>
          <p className="figcap" style={{ margin: "0 0 14px" }}>One point per model for the selected task. Vertical lines are 95% intervals. Up and to the left is better value.</p>
          <CostScoreChart task={task} />
          <p className="figcap">Score on the vertical axis. Cost per 1k items on a log scale; baselines cost under $0.01 and sit at the left edge.</p>
        </figure>
      </div>
      <ErrorExamples examples={data.errorExamples} />
    </div>
  );
}
