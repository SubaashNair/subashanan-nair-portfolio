"use client";

import { useState, useSyncExternalStore } from "react";

import { ToggleGroup } from "@/components/ui/toggle-group";
import { EXPERIMENT_CATEGORIES, listedExperiments } from "@/content/experiments";

import { ToolItem } from "./tool-item";

const ALL = "all";
const noop = () => () => {};

export function ExperimentList() {
  // False on the server and true in the browser, so a no-JavaScript visitor sees every tool and no dead buttons.
  const hydrated = useSyncExternalStore(noop, () => true, () => false);
  const [filter, setFilter] = useState<ReadonlySet<string>>(new Set([ALL]));

  const active = [...filter][0] ?? ALL;
  const shown = active === ALL ? listedExperiments : listedExperiments.filter((e) => e.category === active);

  return (
    <>
      {hydrated && (
        <>
          <ToggleGroup
            label="Filter by category"
            mode="single"
            className="filters"
            pressed={filter}
            onChange={setFilter}
            items={[{ id: ALL, label: "All" }, ...EXPERIMENT_CATEGORIES.map((c) => ({ id: c.id, label: c.label }))]}
          />
          <p className="count" aria-live="polite">Showing {shown.length} of {listedExperiments.length} tools</p>
        </>
      )}
      <ul className="tools">{shown.map((e) => <ToolItem key={e.name} experiment={e} />)}</ul>
    </>
  );
}
