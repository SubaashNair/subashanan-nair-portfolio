import Link from "next/link";

import { ToolItem } from "@/components/experiments/tool-item";
import { experiments } from "@/content/experiments";

const PREVIEW = ["documentation-mcp-server", "matomari", "exam-monitor-app", "pima-diabetes-mlflow"];

export function ToolsPreview() {
  const shown = experiments.filter((e) => PREVIEW.includes(e.name));
  return (
    <section className="block" aria-labelledby="exp-h" style={{ paddingTop: 0 }}>
      <div className="wrap">
        <h2 id="exp-h">Tools and experiments</h2>
        <p className="intro">Smaller things I have shipped. Each gets its own tile.</p>
        <ul className="tools">{shown.map((e) => <ToolItem key={e.name} experiment={e} />)}</ul>
        <p className="more"><Link className="btn ink" href="/experiments">See all tools and experiments</Link></p>
      </div>
    </section>
  );
}
