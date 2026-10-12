import type { StudyRecord } from "@/content/types";

export function FigurePending({ study }: { study: StudyRecord }) {
  return (
    <div className="tile-frame">
      <h3 className="panel-title">The analysis is in progress</h3>
      <p>When the first run is published, this chapter will show {study.figurePlan}</p>
      <p className="note">Nothing here is estimated or illustrative. Results appear only after the pipeline publishes them with their sources.</p>
    </div>
  );
}
