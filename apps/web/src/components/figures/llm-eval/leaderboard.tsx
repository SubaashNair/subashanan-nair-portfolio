import type { EvalTask } from "@/content/types";
import { palette } from "@/styles/palette";

import { ROLE_COLOUR, ROLE_TINT } from "./role-style";

// Interval bars sit on a 0 to 100 track, the share of questions answered with the latest figure.
export function Leaderboard({ task }: { task: EvalTask }) {
  return (
    <div className="tile-frame">
      <div className="table-wrap" role="region" aria-label="Leaderboard for the selected task" tabIndex={0}>
        <table>
          <thead>
            <tr>
              <th scope="col">Model</th>
              <th scope="col" className="board-metric">{task.metric}, with 95% interval</th>
              <th scope="col" className="num">Tool calls per answer</th>
              <th scope="col" className="num">Median time per answer</th>
            </tr>
          </thead>
          <tbody>
            {task.rows.map((r) => (
              <tr key={r.model}>
                <th scope="row"><span className="model-name"><span className="sw" style={{ background: ROLE_COLOUR[r.role], borderColor: palette.ink }} />{r.model}</span></th>
                <td>
                  <div className="ci">
                    <b>{r.score}<small>{r.low} to {r.high}</small></b>
                    <span className="ci-track" aria-hidden="true">
                      <span className="ci-range" style={{ left: `${r.low}%`, width: `${r.high - r.low}%`, background: ROLE_TINT[r.role] }} />
                      <span className="ci-dot" style={{ left: `${r.score}%`, background: ROLE_COLOUR[r.role] }} />
                    </span>
                  </div>
                </td>
                <td className="num">{r.callsLabel}</td>
                <td className="num">{r.latency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
