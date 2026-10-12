import { Tile } from "@/components/tiles/tile";
import { mixedTile } from "@/components/tiles/tile-geometry";
import { EXPERIMENT_CATEGORIES, experimentUrl } from "@/content/experiments";
import type { ExperimentRecord } from "@/content/types";

export function ToolItem({ experiment }: { experiment: ExperimentRecord }) {
  const category = EXPERIMENT_CATEGORIES.find((c) => c.id === experiment.category)?.inline ?? "";
  return (
    <li className="tool">
      <Tile spec={mixedTile(experiment.tile)} />
      <div>
        <h3>{experiment.private ? experiment.name : <a href={experimentUrl(experiment.name)}>{experiment.name}</a>}</h3>
        <div className="lang">{experiment.language}, {category}{experiment.private && ", private repository"}</div>
        <p>{experiment.description}</p>
      </div>
    </li>
  );
}
