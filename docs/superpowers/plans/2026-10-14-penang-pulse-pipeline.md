# Penang Pulse Real-Results Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Penang Pulse illustrative fixture with real results: a tested Python pipeline computes road distances from every populated 100 m cell in Penang to the nearest public clinic, school and Rapid Penang stop and writes one validated results file; the site publishes it with a new schools and transit table, and the CV quotes it.

**Architecture:** A new package `analysis/pulse/` in the existing uv workspace: `sources` (cached, checksummed downloads), `load` (CSVs, GTFS, district outlines, DOSM totals), `population` (WorldPop and Meta rasters rescaled to DOSM), `roads` (pyosmium graph, bridges, towns), `distance` (snapping, one multi-source Dijkstra per category, bands), `geometry` (the to-scale 600 by 500 map), `export` (templates and the results JSON), `pipeline` (pure orchestration, tested end to end on a synthetic world) and `cli` (downloads, manifest, writing). The site validates `apps/web/src/content/results/penang-pulse.json` with a hand-written guard at import time, so a bad file fails `next build`.

**Tech Stack:** Python 3.12, uv 0.11.4, numpy, scipy, networkx 3.7, osmium (pyosmium) 4.3.1, pyarrow 26.0.0, rasterio 1.5.2 (GDAL 3.12.2 in the wheel), shapely 2.2.0 (GEOS 3.14.1 in the wheel), pytest. Next.js 16.4, React 19.2, TypeScript 5.9, Vitest 4. PyMuPDF 1.26.7 for the CV, run with `uv run --no-project --with`.

**Spec:** `docs/superpowers/specs/2026-10-14-penang-pulse-pipeline-design.md` (approved 2026-10-14). Brief: `.context/pulse-planning-brief.md`. Conventions follow `docs/superpowers/plans/2026-10-13-forecasting-lab-pipeline.md`.

## Global Constraints

- Honesty rule: no hand-typed numbers in site or CV copy that come from results. Every result on the site and in the CV comes from `apps/web/src/content/results/penang-pulse.json`, which only the pipeline writes; prose comes from templates in `analysis/pulse/export.py`. Only `apps/web/src/lib/study-results.ts` branches on `NODE_ENV`.
- Copy rules: sentence case, no em or en dashes in prose, no arrows, no all-caps labels.
- Files under 400 lines. Immutable patterns in TypeScript. Python is typed, with small functions, and reports progress with stdlib `logging`.
- Never commit raw data (`analysis/data/raw/`, which holds the cache `analysis/data/raw/pulse/`), `.env*`, `.vercel/`, `.context/`, `.superpowers/`, `apps/web/next-env.d.ts` or the full CV.
- Spec section 14 is binding: the WorldPop 2020 constrained UN-adjusted grid is the main surface; the Geofabrik PBF, not Overpass; pyosmium and networkx, not OSMnx; roads are undirected and footpaths excluded; all 432 schools, the 32 private ones included.
- Dependency pins, verified on 2026-10-14 with Python 3.12 (macOS arm64; the lock also carries manylinux x86_64 wheels for all five, so CI installs from wheels): `networkx==3.7`, `osmium==4.3.1`, `pyarrow==26.0.0`, `rasterio==1.5.2`, `shapely==2.2.0`.
- Python tests run offline on synthetic fixtures written into pytest's temporary directories. No test reads `/tmp/pp`, `analysis/data/raw/` or the network.
- Distance bands: under 1,000 m; 1,000 to 3,000 m inclusive; over 3,000 m.
- Web checks from the repository root: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`. One web test file: `npm test --workspace web -- src/path/to/file.test.ts`. Python checks from `analysis/`: `uv run pytest` (CI runs `uv sync --locked` first).
- `apps/web/AGENTS.md` applies to web code: read the relevant guide in `node_modules/next/dist/docs/` before using a Next.js API.
- Every test is written first and seen to fail before the code that makes it pass.
- Work on branch `penang-pulse-pipeline`, a git worktree: never run a bare `git stash`. One conventional commit per task.

## Review Focus

The five input conditions the spec implies but does not test that are most likely to bite, most likely first. Each has a test in the task that owns the code.

1. **Bridge ways continue onto land.** In OpenStreetMap the ways named after both bridges include on-land approach roads and mainland flyovers (checked 2026-10-14: the second bridge's named motorway runs inland past 100.46 E). Expected: only the span over water is drawn. Test: Task 7, `test_bridges_are_drawn_only_over_water`.
2. **Meta's raster is float64 with NaN for nodata, inside a zip.** Expected: NaN pixels hold nobody, and the 17.4 GB GeoTIFF is read in place by window (2.8 s for Penang on 2026-10-14). Test: Task 4, `test_the_meta_raster_is_read_inside_its_zip_and_nan_is_nobody`.
3. **A facility whose nearest road is a dropped fragment.** Expected: it snaps to the largest connected component and its distance counts, rather than vanishing or raising. Test: Task 6, `test_a_facility_beside_a_dropped_fragment_snaps_to_the_main_network`.
4. **Swapped or zero coordinates in a facility CSV.** A row with X and Y transposed, or 0 and 0, parses as numbers and would otherwise be kept as "outside every district" and plotted off the map. Expected: the run stops and names the file and line. Test: Task 3, `test_a_clinic_with_bad_coordinates_stops_the_run`.
5. **Two place nodes share a town's name.** OSM has neighbourhoods named after towns (for example the Bayan Lepas free industrial zones). Expected: the town or city node wins over a neighbourhood. Test: Task 5, `test_a_town_beats_a_neighbourhood_with_the_same_name`.

## Before you start

- The spec is committed (`39b0cab`), and this plan is committed after it.
- `apps/web/next-env.d.ts` flips between `./.next/dev/types/...` and `./.next/types/...` whenever `next dev` or `next build` runs. Never stage it. Restore it with `git checkout -- apps/web/next-env.d.ts` before Task 10, which needs a clean tree.
- uv 0.11.4 is installed and `analysis/.venv` exists. Python 3.12 comes from `requires-python`.
- Sources were checked on 2026-10-14; the checksums in Task 3 are from that check.

## File map

```
.github/workflows/ci.yml                               unchanged: the analysis job already runs uv sync --locked and uv run pytest
analysis/
  pyproject.toml, uv.lock                              five new pinned dependencies (Task 3)
  pulse/__init__.py                                    empty (Task 3)
  pulse/sources.py                                     source URLs, checksums, cached downloads, Geofabrik date (Task 3)
  pulse/load.py                                        facilities, stops, district outlines, DOSM totals (Task 3)
  pulse/population.py                                  WorldPop and Meta cells rescaled to DOSM (Task 4)
  pulse/roads.py                                       PBF road graph, bridges, town nodes (Task 5)
  pulse/distance.py                                    snapping, multi-source Dijkstra, bands, rounding (Task 6)
  pulse/geometry.py                                    to-scale map geometry and points (Task 7)
  pulse/export.py                                      prose templates and the results JSON (Task 8)
  pulse/pipeline.py                                    the pure end-to-end run (Task 9)
  pulse/cli.py                                         entry point and manifest (Task 9)
  tests/pulse/__init__.py                              empty (Task 3)
  tests/pulse/world.py                                 the synthetic Penang the tests share (Tasks 3, 4, 5 and 9)
  tests/pulse/conftest.py, contract.py                 shared run fixture; Python mirror of the web validator (Task 9)
  tests/pulse/test_sources.py, test_load.py            (Task 3)
  tests/pulse/test_population.py                       (Task 4)
  tests/pulse/test_roads.py                            (Task 5)
  tests/pulse/test_distance.py                         (Task 6)
  tests/pulse/test_geometry.py                         (Task 7)
  tests/pulse/test_export.py                           (Task 8)
  tests/pulse/test_pipeline.py, test_cli.py            (Task 9)
  tools/update_cv.py, tests/test_update_cv.py          Penang Pulse bullet and tech line (Task 12)
  outputs/penang-pulse-manifest.json                   written by the real run (Task 10)
apps/web/
  public/subashanan-nair-cv.pdf                        updated (Task 12)
  src/app/site.css                                     service table styles (Task 1)
  src/content/types.ts                                 District.far (Task 1)
  src/content/fixtures/penang.ts                       far values (Task 1), source names (Task 11)
  src/components/figures/penang/service-table.tsx, service-table.test.tsx            (Task 1)
  src/components/figures/penang/penang-figure.tsx, penang-figure.test.tsx            table and caption (Task 1)
  src/content/results/parse-checks.ts                  shared validator checks (Task 2)
  src/content/results/parse-forecast.ts                uses the shared checks (Task 2)
  src/content/results/parse-penang.ts, parse-penang.test.ts                          (Task 2)
  src/content/results/penang-pulse.json                written by the real run (Task 10)
  src/content/results/index.ts, index.test.ts          publish the validated file (Task 11)
  src/content/studies.ts                               Penang Pulse record (Task 11)
  src/lib/study-results.test.ts, src/components/study/study-page.test.tsx, study-card.test.tsx   unpublished examples move to llm-eval-lab (Task 11)
```

Not committed: `analysis/data/raw/`, `analysis/.venv/`, `.context/resume/`.

---

### Task 1: Web: the far field, the schools and transit table, and the new caption

**Files:**
- Create: `apps/web/src/components/figures/penang/service-table.tsx`
- Modify: `apps/web/src/content/types.ts`, `apps/web/src/content/fixtures/penang.ts`, `apps/web/src/components/figures/penang/penang-figure.tsx`, `apps/web/src/app/site.css`
- Test: `apps/web/src/components/figures/penang/service-table.test.tsx` (create), `apps/web/src/components/figures/penang/penang-figure.test.tsx` (modify)

**Interfaces:**
- Consumes: `District`, `ServiceCategory`, `PenangResults` (`@/content/types`); `penangFixture` (`@/content/fixtures/penang`).
- Produces: `District.far: Readonly<Record<ServiceCategory, number>>`, the % of a district's residents over 3 km from the nearest clinic, school and transit stop, with `far.clinic === bands[2]`; `ServiceTable({ districts, selected }: { districts: readonly District[]; selected: string })`, a `<table>` with caption "Share of residents more than 3 km by road from the nearest service", one row per district in the given order and the selected row marked `className="on"` and `aria-current="true"`; `penangFixture` with `far` on every district. Task 2 uses the fixture as its valid input; Task 11 checks the table on the published page.

- [ ] **Step 1: Write the failing tests**

Create `apps/web/src/components/figures/penang/service-table.test.tsx`:

```tsx
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { penangFixture } from "@/content/fixtures/penang";

import { ServiceTable } from "./service-table";

describe("ServiceTable", () => {
  it("has a caption, five district rows and three service columns", () => {
    render(<ServiceTable districts={penangFixture.districts} selected="sps" />);
    const table = screen.getByRole("table", { name: /more than 3 km by road from the nearest service/i });
    const [head, ...rows] = within(table).getAllByRole("row");
    expect(within(head).getAllByRole("columnheader").map((c) => c.textContent)).toEqual(["District", "Clinic", "School", "Transit stop"]);
    expect(rows.map((r) => within(r).getByRole("rowheader").textContent)).toEqual(["Timur Laut", "Barat Daya", "SP Utara", "SP Tengah", "SP Selatan"]);
    expect(within(rows[4]).getAllByRole("cell").map((c) => c.textContent)).toEqual(["21%", "11%", "27%"]);
  });

  it("highlights only the selected district", () => {
    const { container } = render(<ServiceTable districts={penangFixture.districts} selected="bd" />);
    const marked = container.querySelectorAll("tbody tr.on");
    expect(marked).toHaveLength(1);
    expect(marked[0]).toHaveAttribute("aria-current", "true");
    expect(within(marked[0] as HTMLElement).getByRole("rowheader")).toHaveTextContent("Barat Daya");
  });
});
```

In `apps/web/src/components/figures/penang/penang-figure.test.tsx`, replace:

```tsx
    expect(container.querySelector('.district.on[data-district="tl"]')).not.toBeNull();
  });
```

with:

```tsx
    expect(container.querySelector('.district.on[data-district="tl"]')).not.toBeNull();
    expect(container.querySelector("tbody tr.on th")).toHaveTextContent("Timur Laut");
  });

  it("captions shares as road distance from populated cells", () => {
    render(<PenangFigure data={penangFixture} />);
    expect(screen.getByText(/by road distance from each populated 100 m cell/)).toBeInTheDocument();
    expect(screen.queryByText(/mukim/)).not.toBeInTheDocument();
  });
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/components/figures/penang`
Expected: FAIL. `service-table.test.tsx` fails with `Failed to resolve import "./service-table"`; in `penang-figure.test.tsx` the selection test fails because `tbody tr.on th` is null, and the caption test fails with `Unable to find an element with the text: /by road distance from each populated 100 m cell/`.

- [ ] **Step 3: Implement**

In `apps/web/src/content/types.ts`, replace:

```ts
  population: number;
}
export interface ServicePoint {
```

with:

```ts
  population: number;
  far: Readonly<Record<ServiceCategory, number>>; // % of residents over 3 km from the nearest clinic, school and transit stop
}
export interface ServicePoint {
```

The fixture stays illustrative and dev-only. In `apps/web/src/content/fixtures/penang.ts`, replace:

```ts
    { id: "tl", name: "Timur Laut", short: "Timur Laut", bands: [72, 24, 4], population: 545000 },
    { id: "bd", name: "Barat Daya", short: "Barat Daya", bands: [48, 34, 18], population: 236000 },
    { id: "spu", name: "Seberang Perai Utara", short: "SP Utara", bands: [55, 33, 12], population: 330000 },
    { id: "spt", name: "Seberang Perai Tengah", short: "SP Tengah", bands: [61, 30, 9], population: 402000 },
    { id: "sps", name: "Seberang Perai Selatan", short: "SP Selatan", bands: [41, 38, 21], population: 205000 },
```

with:

```ts
    { id: "tl", name: "Timur Laut", short: "Timur Laut", bands: [72, 24, 4], population: 545000, far: { clinic: 4, school: 2, transit: 1 } },
    { id: "bd", name: "Barat Daya", short: "Barat Daya", bands: [48, 34, 18], population: 236000, far: { clinic: 18, school: 9, transit: 22 } },
    { id: "spu", name: "Seberang Perai Utara", short: "SP Utara", bands: [55, 33, 12], population: 330000, far: { clinic: 12, school: 6, transit: 15 } },
    { id: "spt", name: "Seberang Perai Tengah", short: "SP Tengah", bands: [61, 30, 9], population: 402000, far: { clinic: 9, school: 4, transit: 8 } },
    { id: "sps", name: "Seberang Perai Selatan", short: "SP Selatan", bands: [41, 38, 21], population: 205000, far: { clinic: 21, school: 11, transit: 27 } },
```

Create `apps/web/src/components/figures/penang/service-table.tsx`:

```tsx
import type { District, ServiceCategory } from "@/content/types";

const COLUMNS: ReadonlyArray<{ id: ServiceCategory; label: string }> = [
  { id: "clinic", label: "Clinic" },
  { id: "school", label: "School" },
  { id: "transit", label: "Transit stop" },
];

// Share of each district's residents more than 3 km by road from each service. Rows keep the fixed district order.
export function ServiceTable({ districts, selected }: { districts: readonly District[]; selected: string }) {
  return (
    <div className="table-wrap service-table" role="region" aria-labelledby="service-caption" tabIndex={0}>
      <table>
        <caption id="service-caption">Share of residents more than 3 km by road from the nearest service</caption>
        <thead>
          <tr>
            <th scope="col">District</th>
            {COLUMNS.map((c) => <th key={c.id} scope="col" className="num">{c.label}</th>)}
          </tr>
        </thead>
        <tbody>
          {districts.map((d) => (
            <tr key={d.id} className={d.id === selected ? "on" : undefined} aria-current={d.id === selected ? "true" : undefined}>
              <th scope="row">{d.short}</th>
              {COLUMNS.map((c) => <td key={c.id} className="num">{d.far[c.id]}%</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

In `apps/web/src/components/figures/penang/penang-figure.tsx`, replace:

```tsx
import { CATEGORY_COLOUR, PenangMap } from "./penang-map";
```

with:

```tsx
import { CATEGORY_COLOUR, PenangMap } from "./penang-map";
import { ServiceTable } from "./service-table";
```

Then, in the same file, replace:

```tsx
          <DistrictPanel district={district} />
          <p className="figcap"><abbr title="Seberang Perai">SP</abbr> is Seberang Perai. Shares are of residents, by road distance from population-weighted mukim centroids.</p>
```

with:

```tsx
          <DistrictPanel district={district} />
          <ServiceTable districts={data.districts} selected={district.id} />
          <p className="figcap"><abbr title="Seberang Perai">SP</abbr> is Seberang Perai. Shares are of residents, by road distance from each populated 100 m cell.</p>
```

The table sits directly in the dark evidence chapter, which sets light text, so it takes the ink colour itself (a render during planning showed white on white without it). The global `table` rule's `min-width: 640px` and 16 px cell padding are too wide for the figure column; with 12 px padding all four columns fit at 390 px. In `apps/web/src/app/site.css`, replace:

```css
.panel .callout strong { font-size: 22px; display: block; }
```

with:

```css
.panel .callout strong { font-size: 22px; display: block; }
.service-table { margin-top: 22px; color: var(--ink); }
.service-table table { min-width: 0; }
.service-table th, .service-table td { padding: 10px 12px; }
.service-table tr.on > * { background: rgba(217, 162, 27, .2); font-weight: 650; }
```

`site.css` was already 423 lines before this task; the four lines sit with the other district panel rules rather than in a new file, matching how the rest of the site is styled.

- [ ] **Step 4: Run the tests and checks**

Run: `npm test --workspace web -- src/components/figures/penang`, then `npm test`, `npm run typecheck` and `npm run lint`.
Expected: the three Penang figure files pass; overall `Tests  125 passed (125)`; no type or lint errors.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/content/types.ts apps/web/src/content/fixtures/penang.ts apps/web/src/app/site.css \
  apps/web/src/components/figures/penang/service-table.tsx apps/web/src/components/figures/penang/service-table.test.tsx \
  apps/web/src/components/figures/penang/penang-figure.tsx apps/web/src/components/figures/penang/penang-figure.test.tsx
git commit -m "feat: add the Penang Pulse schools and transit table"
```

---

### Task 2: Web: validate Penang Pulse results files

**Files:**
- Create: `apps/web/src/content/results/parse-checks.ts`, `apps/web/src/content/results/parse-penang.ts`
- Modify: `apps/web/src/content/results/parse-forecast.ts` (use the shared checks; behaviour unchanged)
- Test: `apps/web/src/content/results/parse-penang.test.ts` (create); `parse-forecast.test.ts` must keep passing unchanged

**Interfaces:**
- Consumes: `PenangResults`, `ServiceCategory`, `ForecastResults`, `ForecastModelId` (`content/types.ts`); `penangFixture` (Task 1) as the valid example.
- Produces: `checks(study: string)` returning `{ fail, object, text, isoDate, finite, whole, list, numbers, base }`, each throwing `Error("<study> results: <path> <problem>")` on the first problem; `parsePenangResults(json: unknown): PenangResults`, which returns its input typed when every check passes. It enforces: the base fields; exactly the districts `tl, bd, spu, spt, sps` in that order; whole-number bands from 0 to 100 that sum to 100; a positive whole population; whole `far` values for clinic, school and transit with `far.clinic` equal to `bands[2]`; at least one point, each with a known category and finite x and y; outlines and boundaries that are SVG paths; exactly 2 bridges and 6 places; a water label; a points note. Task 11 calls it on the committed JSON. `parseForecastResults` keeps its exact messages.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/content/results/parse-penang.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { penangFixture } from "../fixtures/penang";
import { parsePenangResults } from "./parse-penang";

// The fixture, as plain JSON, is a valid file. Each malformed case changes one thing in a copy.
const valid = JSON.parse(JSON.stringify(penangFixture));
const district = valid.districts[0];
const withDistrict = (changes: object) => ({ ...valid, districts: [{ ...district, ...changes }, ...valid.districts.slice(1)] });
const withGeometry = (changes: object) => ({ ...valid, geometry: { ...valid.geometry, ...changes } });

describe("parsePenangResults", () => {
  it("accepts a valid file and returns its data", () => {
    const parsed = parsePenangResults(valid);
    expect(parsed.districts.map((d) => d.id)).toEqual(["tl", "bd", "spu", "spt", "sps"]);
    expect(parsed.districts[4].far).toEqual({ clinic: 21, school: 11, transit: 27 });
    expect(parsed.points).toHaveLength(penangFixture.points.length);
  });

  it.each([
    ["not an object", null, /file must be an object/],
    ["a missing answer", { ...valid, answer: "" }, /answer must be a non-empty string/],
    ["four districts", { ...valid, districts: valid.districts.slice(1) }, /districts must have 5 items/],
    ["districts out of order", { ...valid, districts: [valid.districts[1], valid.districts[0], ...valid.districts.slice(2)] }, /districts\[0\]\.id must be tl/],
    ["bands that do not sum to 100", withDistrict({ bands: [72, 24, 5] }), /districts\[0\]\.bands must sum to 100/],
    ["a fractional band", withDistrict({ bands: [71.5, 24.5, 4] }), /districts\[0\]\.bands\[0\] must be a whole number/],
    ["a missing far value", withDistrict({ far: { clinic: 4, school: 2 } }), /districts\[0\]\.far\.transit/],
    ["a far clinic share that disagrees with the bands", withDistrict({ far: { ...district.far, clinic: 5 } }), /far\.clinic must equal the over 3 km band/],
    ["a population of zero", withDistrict({ population: 0 }), /districts\[0\]\.population/],
    ["no points", { ...valid, points: [] }, /points must have at least one point/],
    ["a point with an unknown category", { ...valid, points: [{ category: "hospital", x: 1, y: 1 }] }, /points\[0\]\.category/],
    ["one bridge", withGeometry({ bridges: valid.geometry.bridges.slice(1) }), /geometry\.bridges must have 2 items/],
    ["five places", withGeometry({ places: valid.geometry.places.slice(1) }), /geometry\.places must have 6 items/],
    ["an island outline that is not a path", withGeometry({ island: "Z" }), /geometry\.island must be an SVG path/],
    ["a district outline on unknown land", withGeometry({ districts: [{ ...valid.geometry.districts[0], land: "sea" }, ...valid.geometry.districts.slice(1)] }), /geometry\.districts\[0\]\.land/],
  ])("rejects %s", (_name, input, message) => {
    expect(() => parsePenangResults(input)).toThrow(message);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test --workspace web -- src/content/results/parse-penang.test.ts`
Expected: FAIL with `Failed to resolve import "./parse-penang"`.

- [ ] **Step 3: Extract the shared checks and write the validator**

The forecasting validator's helpers move into a shared module so both validators use one implementation. Each helper returns its value or the result of `fail`, so callers never depend on `never` narrowing through a destructured function.

Create `apps/web/src/content/results/parse-checks.ts`:

```ts
// Shared checks for the results validators. Each validator makes its own set, so errors name the study.
// Every check throws on the first problem, so a bad file fails the build instead of reaching a page.
export type Json = Record<string, unknown>;

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export function checks(study: string) {
  const fail = (path: string, problem: string): never => {
    throw new Error(`${study} results: ${path} ${problem}`);
  };

  const object = (value: unknown, path: string): Json => {
    if (typeof value !== "object" || value === null || Array.isArray(value)) return fail(path, "must be an object");
    return value as Json;
  };

  const text = (value: unknown, path: string): string => {
    if (typeof value !== "string" || value.trim() === "") return fail(path, "must be a non-empty string");
    return value;
  };

  const isoDate = (value: unknown, path: string): string => {
    const date = text(value, path);
    return ISO_DATE.test(date) ? date : fail(path, "must be a YYYY-MM-DD date");
  };

  const finite = (value: unknown, path: string): number => {
    if (typeof value !== "number" || !Number.isFinite(value)) return fail(path, "must be a finite number");
    return value;
  };

  const whole = (value: unknown, path: string, min: number, max: number): number => {
    const n = finite(value, path);
    return Number.isInteger(n) && n >= min && n <= max ? n : fail(path, `must be a whole number from ${min} to ${max}`);
  };

  const list = (value: unknown, path: string, length?: number): unknown[] => {
    if (!Array.isArray(value)) return fail(path, "must be an array");
    if (length !== undefined && value.length !== length) return fail(path, `must have ${length} items, found ${value.length}`);
    return value;
  };

  const numbers = (value: unknown, path: string, length?: number): number[] => list(value, path, length).map((v, i) => finite(v, `${path}[${i}]`));

  // The fields every study's results share: answer, key numbers, run and retrieval dates.
  const base = (root: Json): void => {
    text(root.answer, "answer");
    list(root.keyNumbers, "keyNumbers", 3).forEach((n, i) => {
      const k = object(n, `keyNumbers[${i}]`);
      for (const field of ["value", "label", "caveat"]) text(k[field], `keyNumbers[${i}].${field}`);
    });
    const run = object(root.run, "run");
    for (const field of ["commit", "manifest", "python"]) text(run[field], `run.${field}`);
    isoDate(run.lastRun, "run.lastRun");
    const retrieved = object(root.retrieved, "retrieved");
    if (Object.keys(retrieved).length === 0) fail("retrieved", "must name at least one source");
    for (const [name, date] of Object.entries(retrieved)) isoDate(date, `retrieved.${name}`);
  };

  return { fail, object, text, isoDate, finite, whole, list, numbers, base };
}
```

Replace `apps/web/src/content/results/parse-forecast.ts` with:

```ts
import type { ForecastModelId, ForecastResults } from "../types";
import { checks, type Json } from "./parse-checks";

// Checks a results file against the ForecastResults shape and the chart contract before the site uses it.
const MODEL_IDS: readonly ForecastModelId[] = ["persistence", "seasonal", "gb", "mlp", "chronos"];
const { fail, object, text, finite, list, numbers, base } = checks("forecasting-lab");

function checkModels(root: Json, horizons: number): void {
  const ids = list(root.models, "models").map((m, i) => {
    const model = object(m, `models[${i}]`);
    text(model.name, `models[${i}].name`);
    numbers(model.mae, `models[${i}].mae`, horizons);
    return model.id;
  });
  if (ids.length !== MODEL_IDS.length || MODEL_IDS.some((id) => !ids.includes(id))) fail("models", `must list each of ${MODEL_IDS.join(", ")} once`);
}

function checkSensor(value: unknown, path: string): void {
  const s = object(value, path);
  text(s.id, `${path}.id`);
  text(s.label, `${path}.label`);
  const origin = finite(s.originMinutes, `${path}.originMinutes`);
  if (!Number.isInteger(origin) || origin < 0 || origin >= 24 * 60) fail(`${path}.originMinutes`, "must be a whole minute of the day");
  if (finite(s.stepMinutes, `${path}.stepMinutes`) <= 0) fail(`${path}.stepMinutes`, "must be positive");
  const past = finite(s.pastSteps, `${path}.pastSteps`);
  if (!Number.isInteger(past) || past < 1) fail(`${path}.pastSteps`, "must be a positive whole number");
  const ahead = numbers(s.actual, `${path}.actual`).length - past - 1;
  if (ahead < 1) fail(`${path}.actual`, "must cover the past steps, the origin and at least one step ahead");
  const forecasts = object(s.forecasts, `${path}.forecasts`);
  const windowMae = object(s.windowMae, `${path}.windowMae`);
  for (const id of MODEL_IDS) {
    numbers(forecasts[id], `${path}.forecasts.${id}`, ahead + 1);
    finite(windowMae[id], `${path}.windowMae.${id}`);
  }
}

export function parseForecastResults(json: unknown): ForecastResults {
  const root = object(json, "file");
  base(root);
  const horizons = numbers(root.horizons, "horizons");
  if (horizons.length === 0 || horizons.some((h) => h <= 0)) fail("horizons", "must be positive minutes");
  checkModels(root, horizons.length);
  const sensors = list(root.sensors, "sensors");
  if (sensors.length === 0) fail("sensors", "must have at least one sensor");
  sensors.forEach((s, i) => checkSensor(s, `sensors[${i}]`));
  return root as unknown as ForecastResults;
}
```

Create `apps/web/src/content/results/parse-penang.ts`:

```ts
import type { PenangResults, ServiceCategory } from "../types";
import { checks, type Json } from "./parse-checks";

// Checks a results file against the PenangResults shape before the site uses it.
const DISTRICT_IDS = ["tl", "bd", "spu", "spt", "sps"] as const;
const CATEGORIES: readonly ServiceCategory[] = ["clinic", "school", "transit"];
const LANDS = ["island", "mainland"];
const BRIDGES = 2;
const PLACES = 6;
const { fail, object, text, finite, whole, list, base } = checks("penang-pulse");

function checkDistrict(value: unknown, i: number): void {
  const path = `districts[${i}]`;
  const d = object(value, path);
  if (d.id !== DISTRICT_IDS[i]) fail(`${path}.id`, `must be ${DISTRICT_IDS[i]}, the fixed district order is ${DISTRICT_IDS.join(", ")}`);
  text(d.name, `${path}.name`);
  text(d.short, `${path}.short`);
  const bands = list(d.bands, `${path}.bands`, 3).map((b, j) => whole(b, `${path}.bands[${j}]`, 0, 100));
  if (bands[0] + bands[1] + bands[2] !== 100) fail(`${path}.bands`, "must sum to 100");
  whole(d.population, `${path}.population`, 1, Number.MAX_SAFE_INTEGER);
  const far = object(d.far, `${path}.far`);
  for (const c of CATEGORIES) whole(far[c], `${path}.far.${c}`, 0, 100);
  if (far.clinic !== bands[2]) fail(`${path}.far.clinic`, "must equal the over 3 km band");
}

function checkLabel(value: unknown, path: string): void {
  const label = object(value, path);
  text(label.text, `${path}.text`);
  finite(label.x, `${path}.x`);
  finite(label.y, `${path}.y`);
}

function checkPath(value: unknown, path: string): void {
  if (!text(value, path).startsWith("M")) fail(path, "must be an SVG path starting with M");
}

function checkGeometry(value: unknown): void {
  const g = object(value, "geometry");
  checkPath(g.island, "geometry.island");
  checkPath(g.mainland, "geometry.mainland");
  list(g.districts, "geometry.districts", DISTRICT_IDS.length).forEach((v, i) => {
    const d = object(v, `geometry.districts[${i}]`);
    if (d.id !== DISTRICT_IDS[i]) fail(`geometry.districts[${i}].id`, `must be ${DISTRICT_IDS[i]}`);
    checkPath(d.d, `geometry.districts[${i}].d`);
    if (!LANDS.includes(d.land as string)) fail(`geometry.districts[${i}].land`, "must be island or mainland");
  });
  list(g.boundaries, "geometry.boundaries").forEach((b, i) => checkPath(b, `geometry.boundaries[${i}]`));
  list(g.bridges, "geometry.bridges", BRIDGES).forEach((b, i) => checkPath(b, `geometry.bridges[${i}]`));
  list(g.places, "geometry.places", PLACES).forEach((p, i) => checkLabel(p, `geometry.places[${i}]`));
  checkLabel(g.water, "geometry.water");
}

function checkPoint(value: unknown, i: number): void {
  const p = object(value, `points[${i}]`);
  if (!CATEGORIES.includes(p.category as ServiceCategory)) fail(`points[${i}].category`, `must be one of ${CATEGORIES.join(", ")}`);
  finite(p.x, `points[${i}].x`);
  finite(p.y, `points[${i}].y`);
}

export function parsePenangResults(json: unknown): PenangResults {
  const root: Json = object(json, "file");
  base(root);
  list(root.districts, "districts", DISTRICT_IDS.length).forEach(checkDistrict);
  const points = list(root.points, "points");
  if (points.length === 0) fail("points", "must have at least one point");
  points.forEach(checkPoint);
  checkGeometry(root.geometry);
  text(root.pointsNote, "pointsNote");
  return root as unknown as PenangResults;
}
```

- [ ] **Step 4: Run the tests and checks**

Run: `npm test --workspace web -- src/content/results`, then `npm test`, `npm run typecheck` and `npm run lint`.
Expected: `parse-penang.test.ts` 16 passed and `parse-forecast.test.ts` 13 passed, unchanged; overall `Tests  141 passed (141)`; no type or lint errors.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/content/results/parse-checks.ts apps/web/src/content/results/parse-forecast.ts \
  apps/web/src/content/results/parse-penang.ts apps/web/src/content/results/parse-penang.test.ts
git commit -m "feat: validate Penang Pulse results files"
```

---

### Task 3: Python: dependencies, sources and loaders

**Files:**
- Modify: `analysis/pyproject.toml`, `analysis/uv.lock` (generated)
- Create: `analysis/pulse/__init__.py` (empty), `analysis/pulse/sources.py`, `analysis/pulse/load.py`, `analysis/tests/pulse/__init__.py` (empty), `analysis/tests/pulse/world.py`
- Test: `analysis/tests/pulse/test_sources.py`, `analysis/tests/pulse/test_load.py`

**Interfaces:**
- Consumes: `forecasting.data.sha256_of(path: Path) -> str`.
- Produces, in `pulse.sources`: `Source(name, file, url, licence, sha256, fixed)` (frozen; `name` is the source name the study page lists and the key in the results file's `retrieved`); constants `HEALTH`, `SCHOOLS`, `GTFS`, `DOSM`, `BOUNDARIES`, `WORLDPOP`, `META`, `FILE_SOURCES` (those seven, in that order), `META_MEMBER = "mys_general_2020.tif"`, `OSM_NAME = "OpenStreetMap"`, `OSM_LICENCE`, `GEOFABRIK_DIR`, `GEOFABRIK_LATEST`, `CHECKED_ON`; `Fetched(name, url, licence, path, retrieved, bytes, sha256)`; `download(url, path) -> None`; `retrieved_at(path) -> str`; `fetch(source, raw_dir) -> Fetched`; `geofabrik_date(file_name) -> str` (`YYYY-MM-DD`); `latest_geofabrik_url() -> str`; `fetch_osm(raw_dir) -> Fetched`.
- Produces, in `pulse.load`: `Bounds = tuple[float, float, float, float]` (min lon, min lat, max lon, max lat); `DistrictSpec(id, name, short, land)`; `DISTRICTS` in the fixed order Timur Laut, Barat Daya, SP Utara, SP Tengah, SP Selatan; `CATEGORIES = ("clinic", "school", "transit")`; `AREA_MARGIN_DEG = 0.1`; `Facility(category, lon, lat, year)`; `expand(bounds, margin) -> Bounds`; `inside(bounds, lon, lat) -> bool`; `read_rows(path, required) -> list[dict[str, str]]`; `parse_point(x, y, where) -> tuple[float, float]`; `read_clinics(path, area) -> list[Facility]`; `read_schools(path, area) -> list[Facility]`; `read_stops(gtfs_zip, land) -> list[Facility]`; `load_districts(path) -> list[BaseGeometry]`; `load_totals(path) -> list[int]` (people, in `DISTRICTS` order); `outside_districts(facilities, land) -> dict[str, int]`.
- Produces, in `tests/pulse/world.py`: `BOXES`, `ISLET`, `DECOY`, `THOUSANDS`, `AREA`, `CLINICS`, `SCHOOLS`, `STOPS`, `write_csv`, `write_health(folder, clinics=CLINICS, encoding="utf-8-sig")`, `write_schools(folder, schools=SCHOOLS)`, `write_gtfs(folder, stops=STOPS)`, `district_shapes()`, `write_boundaries(folder, names=None)`, `write_dosm(folder, thousands=THOUSANDS, extra=None)`, each returning the written path. Tasks 4, 5 and 9 extend this file.

The synthetic world is five rectangles on a 0.01 degree grid: an island of Timur Laut (with a small islet, so it is a MultiPolygon) over Barat Daya, a strait one cell wide, and a mainland of SP Utara over SP Tengah over SP Selatan. Real districts are irregular, but the code paths are the same.

- [ ] **Step 1: Add the dependencies and the packages**

In `analysis/pyproject.toml`, replace:

```toml
  "scikit-learn>=1.6,<2",
]
```

with:

```toml
  "scikit-learn>=1.6,<2",
  "networkx==3.7",
  "osmium==4.3.1",
  "pyarrow==26.0.0",
  "rasterio==1.5.2",
  "shapely==2.2.0",
]
```

Create the empty files `analysis/pulse/__init__.py` and `analysis/tests/pulse/__init__.py`.

Run (in `analysis/`): `uv lock`, then `uv sync --locked`, then `uv run python -c "import networkx, osmium, pyarrow, rasterio, shapely; print(rasterio.__gdal_version__, shapely.geos_version_string)"`.
Expected: `uv lock` adds networkx 3.7, osmium 4.3.1, pyarrow 26.0.0, rasterio 1.5.2 and shapely 2.2.0 with their dependencies (affine, attrs, certifi, click, pyparsing, requests and others) and leaves numpy 2.5.4, scipy 1.18.1 and scikit-learn 1.9.1 unchanged; `uv sync --locked` exits 0; the last command prints `3.12.2 3.14.1`.

- [ ] **Step 2: Write the failing tests**

Create `analysis/tests/pulse/world.py`:

```python
"""A tiny synthetic Penang: five rectangular districts on an island and a mainland with a strait between, and the files the loaders read."""

from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import MultiPolygon, box, mapping

BOXES = {  # min lon, min lat, max lon, max lat
    "Timur Laut": (100.20, 5.33, 100.22, 5.36),
    "Barat Daya": (100.20, 5.30, 100.22, 5.33),
    "Seberang Perai Utara": (100.23, 5.34, 100.26, 5.36),
    "Seberang Perai Tengah": (100.23, 5.32, 100.26, 5.34),
    "Seberang Perai Selatan": (100.23, 5.30, 100.26, 5.32),
}
ISLET = (100.222, 5.300, 100.224, 5.302)  # a small island in the strait that belongs to Timur Laut, so one district is a MultiPolygon
DECOY = ("Kuala Muda", (100.40, 5.60, 100.42, 5.62))  # a district in another state, which must be ignored
THOUSANDS = {"Timur Laut": 6.0, "Barat Daya": 3.0, "Seberang Perai Utara": 4.0, "Seberang Perai Tengah": 4.5, "Seberang Perai Selatan": 2.5}
AREA = (100.10, 5.20, 100.36, 5.46)  # the districts' box widened by AREA_MARGIN_DEG

HEALTH_HEADER = ["NAMA", "NO_TEL", "NO_FAKS", "JENIS", "TARIKH_DATA", "NO", "UNIT_TKT", "BANGUNAN", "JALAN", "KG_TMN", "BANDAR", "POSKOD", "DAERAH", "NEGERI", "X", "Y"]
CLINICS = [  # NAMA, JENIS, TARIKH_DATA, DAERAH, X, Y
    ("KLINIK KESIHATAN UTARA", "KLINIK KESIHATAN", "17/02/2021", "SPU", "100.245", "5.355"),
    ("KLINIK DESA BARAT", "KLINIK DESA", "31/12/2013", "DBD", "100.21", "5.305"),
    ("KLINIK PERGIGIAN TIMUR", "KLINIK PERGIGIAN", "01/06/2022", "DTL", "100.21", "5.355"),  # dental, left out
    ("HOSPITAL SEBERANG", "HOSPITAL KERAJAAN", "31/12/2022", "SPS", "100.265", "5.31"),  # just outside every district, kept
]
SCHOOL_HEADER = ["NAM", "TEL", "FAX", "EML", "WEB", "PPD", "KATEGORI", "TARIKH_DATA", "PERINGKAT", "JENIS_LABEL", "ALAMATSURAT", "LOKASI", "JENIS_BANTUAN",
                 "PRASEKOLAH", "INTEGRASI", "NAM_LABEL", "UNIT_TKT", "BANGUNAN", "JALAN", "KG_TMN", "BANDAR", "POSKOD", "DAERAH", "NEGERI", "ID_SKLH", "X", "Y"]
SCHOOLS = [  # NAM, PERINGKAT, JENIS_LABEL, TARIKH_DATA, DAERAH, X, Y
    ("SK TIMUR", "RENDAH", "SK", "31/12/2015", "DTL", "100.215", "5.345"),
    ("SMK TENGAH", "MENENGAH", "SMK", "31/12/2020", "SPT", "100.25", "5.325"),
    ("SEKOLAH SWASTA SELATAN", "TIADA", "SWASTA", "31/12/2018", "SPS", "100.24", "5.305"),
]
STOPS = [("1", "5.325", "100.21"), ("2", "5.335", "100.245"), ("3", "5.40", "100.30")]  # stop_id, stop_lat, stop_lon; the third is outside


def write_csv(path: Path, header: list[str], rows: list[dict[str, str]], encoding: str = "utf-8-sig") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, restval="NA")
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_health(folder: Path, clinics: list[tuple[str, ...]] = CLINICS, encoding: str = "utf-8-sig") -> Path:
    rows = [{"NAMA": n, "JENIS": j, "TARIKH_DATA": t, "DAERAH": d, "NEGERI": "PULAU PINANG", "X": x, "Y": y} for n, j, t, d, x, y in clinics]
    return write_csv(folder / "health.csv", HEALTH_HEADER, rows, encoding)


def write_schools(folder: Path, schools: list[tuple[str, ...]] = SCHOOLS) -> Path:
    rows = [{"NAM": n, "PERINGKAT": p, "JENIS_LABEL": j, "TARIKH_DATA": t, "DAERAH": d, "NEGERI": "PULAU PINANG", "X": x, "Y": y} for n, p, j, t, d, x, y in schools]
    return write_csv(folder / "schools.csv", SCHOOL_HEADER, rows)


def write_gtfs(folder: Path, stops: list[tuple[str, str, str]] = STOPS) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["stop_id,stop_code,stop_name,stop_lat,stop_lon", *(f"{i},S{i},Stop {i},{lat},{lon}" for i, lat, lon in stops)]
    path = folder / "gtfs.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("stops.txt", "\n".join(lines) + "\n")
    return path


def district_shapes() -> dict[str, object]:
    shapes: dict[str, object] = {name: box(*bounds) for name, bounds in BOXES.items()}
    return {**shapes, "Timur Laut": MultiPolygon([box(*BOXES["Timur Laut"]), box(*ISLET)])}


def write_boundaries(folder: Path, names: list[str] | None = None) -> Path:
    shapes = district_shapes()
    chosen = list(BOXES) if names is None else names
    features = [{"type": "Feature", "properties": {"shapeName": n, "shapeType": "ADM2"}, "geometry": mapping(shapes[n])} for n in chosen]
    features.append({"type": "Feature", "properties": {"shapeName": DECOY[0], "shapeType": "ADM2"}, "geometry": mapping(box(*DECOY[1]))})
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "boundaries.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return path


def write_dosm(folder: Path, thousands: dict[str, float] = THOUSANDS, extra: list[dict[str, object]] | None = None) -> Path:
    def row(district: str, population: float, **changes: object) -> dict[str, object]:
        base = {"state": "Pulau Pinang", "district": district, "date": datetime.date(2020, 1, 1), "sex": "both", "age": "overall", "ethnicity": "overall"}
        return {**base, "population": population, **changes}

    rows = [row(d, p) for d, p in thousands.items()]
    decoys = [row("Timur Laut", 9.9, date=datetime.date(2021, 1, 1)), row("Timur Laut", 3.1, sex="male"), row("Kuala Muda", 7.0, state="Kedah")]
    columns = {k: [r[k] for r in [*rows, *decoys, *(extra or [])]] for k in rows[0]}
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "population_district.parquet"
    pq.write_table(pa.table(columns), path)
    return path
```

Create `analysis/tests/pulse/test_sources.py`:

```python
import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path

import pytest

from pulse import sources
from pulse.sources import FILE_SOURCES, Source, fetch, fetch_osm, geofabrik_date


def local_source(tmp_path: Path, content: bytes = b"abc", sha256: str | None = None, fixed: bool = True) -> Source:
    origin = tmp_path / "origin.csv"
    origin.write_bytes(content)
    return Source("Test source", "test.csv", origin.as_uri(), "CC BY", sha256 or hashlib.sha256(content).hexdigest(), fixed)


def test_fetch_downloads_once_and_records_when(tmp_path: Path) -> None:
    source = local_source(tmp_path)
    first = fetch(source, tmp_path / "raw")
    (tmp_path / "origin.csv").unlink()  # the second fetch must use the cache
    second = fetch(source, tmp_path / "raw")

    assert first == second
    assert first.path == tmp_path / "raw/test.csv"
    assert (first.bytes, first.sha256) == (3, hashlib.sha256(b"abc").hexdigest())
    assert datetime.fromisoformat(first.retrieved).utcoffset() is not None
    assert not list((tmp_path / "raw").glob("*.part"))


def test_a_changed_fixed_source_stops_the_run(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Test source: SHA-256 .* differs from 0{64}"):
        fetch(local_source(tmp_path, sha256="0" * 64), tmp_path / "raw")


def test_a_changed_feed_is_logged_and_used(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        fetched = fetch(local_source(tmp_path, sha256="0" * 64, fixed=False), tmp_path / "raw")
    assert "differs from" in caplog.text
    assert fetched.bytes == 3


def test_geofabrik_dates_come_from_the_file_name() -> None:
    assert geofabrik_date("malaysia-singapore-brunei-261013.osm.pbf") == "2026-10-13"
    with pytest.raises(ValueError, match="not a dated"):
        geofabrik_date("malaysia-singapore-brunei-latest.osm.pbf")


def test_the_newest_cached_extract_is_reused_without_asking_geofabrik(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "malaysia-singapore-brunei-261001.osm.pbf").write_bytes(b"old")
    (tmp_path / "malaysia-singapore-brunei-261013.osm.pbf").write_bytes(b"new")
    monkeypatch.setattr(sources, "latest_geofabrik_url", lambda: pytest.fail("asked Geofabrik"))

    fetched = fetch_osm(tmp_path)

    assert fetched.path.name == "malaysia-singapore-brunei-261013.osm.pbf"
    assert fetched.url == "https://download.geofabrik.de/asia/malaysia-singapore-brunei-261013.osm.pbf"
    assert (fetched.name, fetched.licence, fetched.bytes) == ("OpenStreetMap", "ODbL", 3)


def test_every_source_has_a_full_checksum_and_its_own_file() -> None:
    assert all(re.fullmatch(r"[0-9a-f]{64}", s.sha256) for s in FILE_SOURCES)
    assert [s.name for s in FILE_SOURCES if not s.fixed] == ["Rapid Penang GTFS"]
    assert len({s.file for s in FILE_SOURCES}) == len(FILE_SOURCES)
```

Create `analysis/tests/pulse/test_load.py`:

```python
import datetime
from pathlib import Path

import pytest
import shapely

from pulse.load import load_districts, load_totals, outside_districts, read_clinics, read_schools, read_stops

from .world import AREA, CLINICS, write_boundaries, write_dosm, write_gtfs, write_health, write_schools


def test_clinics_leave_out_dental_and_keep_one_across_the_boundary(tmp_path: Path) -> None:
    clinics = read_clinics(write_health(tmp_path), AREA)
    assert [(c.category, c.lon, c.lat, c.year) for c in clinics] == [
        ("clinic", 100.245, 5.355, 2021),
        ("clinic", 100.21, 5.305, 2013),
        ("clinic", 100.265, 5.31, 2022),
    ]


def test_schools_include_private_ones(tmp_path: Path) -> None:
    assert [(s.lon, s.lat, s.year) for s in read_schools(write_schools(tmp_path), AREA)] == [(100.215, 5.345, 2015), (100.25, 5.325, 2020), (100.24, 5.305, 2018)]


def test_a_file_without_a_byte_order_mark_reads_the_same(tmp_path: Path) -> None:
    assert read_clinics(write_health(tmp_path / "a"), AREA) == read_clinics(write_health(tmp_path / "b", encoding="utf-8"), AREA)


@pytest.mark.parametrize(
    ("x", "y", "problem"),
    [("NA", "5.3", "bad coordinates"), ("", "5.3", "bad coordinates"), ("nan", "5.3", "bad coordinates"), ("5.305", "100.21", "not in the Penang area"), ("0", "0", "not in the Penang area")],
)
def test_a_clinic_with_bad_coordinates_stops_the_run(tmp_path: Path, x: str, y: str, problem: str) -> None:
    rows = [CLINICS[0], ("KLINIK DESA RUSAK", "KLINIK DESA", "31/12/2013", "DBD", x, y)]
    with pytest.raises(ValueError, match=f"health.csv line 3: .*{problem}"):
        read_clinics(write_health(tmp_path, rows), AREA)


def test_a_missing_column_is_named(tmp_path: Path) -> None:
    path = tmp_path / "health.csv"
    path.write_text("NAMA,JENIS,TARIKH_DATA,LONGITUD,Y\nK,KLINIK DESA,31/12/2013,100.21,5.305\n", encoding="utf-8-sig")
    with pytest.raises(ValueError, match=r"health.csv is missing columns \['X'\]"):
        read_clinics(path, AREA)


def test_stops_outside_every_district_are_left_out(tmp_path: Path) -> None:
    land = shapely.union_all(load_districts(write_boundaries(tmp_path)))
    assert [(s.category, s.lon, s.lat, s.year) for s in read_stops(write_gtfs(tmp_path), land)] == [("transit", 100.21, 5.325, None), ("transit", 100.245, 5.335, None)]


def test_districts_are_chosen_by_name_in_the_fixed_order(tmp_path: Path) -> None:
    shapes = load_districts(write_boundaries(tmp_path))
    assert [s.geom_type for s in shapes] == ["MultiPolygon", "Polygon", "Polygon", "Polygon", "Polygon"]
    assert [round(s.centroid.y, 3) for s in shapes[2:]] == [5.35, 5.33, 5.31]


def test_a_missing_district_is_named(tmp_path: Path) -> None:
    path = write_boundaries(tmp_path, names=["Timur Laut", "Barat Daya", "Seberang Perai Utara", "Seberang Perai Tengah"])
    with pytest.raises(ValueError, match=r"no district named \['Seberang Perai Selatan'\]"):
        load_districts(path)


def test_totals_are_2020_people_for_both_sexes(tmp_path: Path) -> None:
    assert load_totals(write_dosm(tmp_path)) == [6000, 3000, 4000, 4500, 2500]


def test_a_missing_or_doubled_total_stops_the_run(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"no 2020 total for \['Barat Daya'\]"):
        load_totals(write_dosm(tmp_path / "a", {"Timur Laut": 6.0, "Seberang Perai Utara": 4.0, "Seberang Perai Tengah": 4.5, "Seberang Perai Selatan": 2.5}))
    doubled = write_dosm(tmp_path / "b", extra=[{"state": "Pulau Pinang", "district": "Barat Daya", "date": datetime.date(2020, 1, 1), "sex": "both", "age": "overall", "ethnicity": "overall", "population": 1.0}])
    with pytest.raises(ValueError, match="more than one 2020 total for Barat Daya"):
        load_totals(doubled)


def test_facilities_outside_every_district_are_counted(tmp_path: Path) -> None:
    land = shapely.union_all(load_districts(write_boundaries(tmp_path)))
    clinics = read_clinics(write_health(tmp_path), AREA)
    assert outside_districts(clinics, land) == {"clinic": 1, "school": 0, "transit": 0}
```

- [ ] **Step 3: Run the tests to verify they fail**

Run (in `analysis/`): `uv run pytest tests/pulse`
Expected: 2 errors during collection: `ImportError: cannot import name 'sources' from 'pulse'` and `ModuleNotFoundError: No module named 'pulse.load'`.

- [ ] **Step 4: Write the sources and the loaders**

Downloads go through a `.part` file so an interrupted download never looks complete. A fixed source with a different checksum stops the run; the GTFS feed, which the publisher overwrites in place, only logs it. The Geofabrik `-latest` URL answers `307` with the dated file name (checked 2026-10-14: `malaysia-singapore-brunei-261013.osm.pbf`), so the code reads that redirect with a HEAD request and downloads the dated file; a later run reuses the newest cached extract, so reruns use the same roads.

Create `analysis/pulse/sources.py`:

```python
"""Where each Penang Pulse input comes from, and a cached, checksummed download of each file."""

from __future__ import annotations

import logging
import re
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from forecasting.data import sha256_of

log = logging.getLogger(__name__)

USER_AGENT = "observatory-analysis/0.1 (Penang Pulse study)"
CHECKED_ON = "2026-10-14"


@dataclass(frozen=True)
class Source:
    name: str  # the name the study page lists, and the key in the results file's `retrieved`
    file: str  # cache file name in the raw directory
    url: str
    licence: str
    sha256: str  # as checked on CHECKED_ON
    fixed: bool  # False for files the publisher overwrites in place: a different checksum is then logged, not fatal


HEALTH = Source(
    "Public health facilities 2022",
    "pusat_kesihatan_awam_2022_p.csv",
    "https://archive.data.gov.my/data/dataset/20a4c459-5329-450a-8cad-938957f2eefe/resource/95ed70e3-955f-43a8-a99d-072accc49ed0/download/_202310251223490_pusat_kesihatan_awam_2022_p.csv",
    "CC BY",
    "30d7abe179258b20944c775605d9a466bfb8f92c519e5f586d52961848742f68",
    True,
)
SCHOOLS = Source(
    "Schools 2022",
    "be0010_sekolah_2022_p.csv",
    "https://archive.data.gov.my/data/dataset/13d6b29c-2460-4f3e-ba6e-5fb58e407e15/resource/0566082a-6a70-4f2e-9f8c-bd587d2f8cb0/download/_202310251214180_be0010_sekolah_2022_p.csv",
    "CC BY",
    "dc84127ba313d11d0fe70b2ae8f6d70221dbede4077a90f0b2c843fd483e734e",
    True,
)
GTFS = Source(
    "Rapid Penang GTFS",
    "rapid_bus_penang_gtfs.zip",
    "https://api.data.gov.my/gtfs-static/prasarana?category=rapid-bus-penang",
    "CC BY 4.0",
    "9823a7c793108805560a826070ca9c89089c685f9d28c8869337b425aa669c73",
    False,
)
DOSM = Source(
    "Population by district",
    "population_district.parquet",
    "https://storage.dosm.gov.my/population/population_district.parquet",
    "CC BY 4.0",
    "456bca234306c740c523753c62630d409c8713c82cd94b596074a7ca3a024742",
    True,
)
BOUNDARIES = Source(
    "geoBoundaries MYS ADM2",
    "geoBoundaries-MYS-ADM2.geojson",
    "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/9469f09592ced973a3448cf66b6100b741b64c0d/releaseData/gbOpen/MYS/ADM2/geoBoundaries-MYS-ADM2.geojson",
    "CC BY 3.0",
    "1a7db3b44563073171b02eba59b109fc1bc6256ab0b011531ea6d5053515e550",
    True,
)
WORLDPOP = Source(
    "WorldPop 2020 constrained",
    "mys_ppp_2020_UNadj_constrained.tif",
    "https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/MYS/mys_ppp_2020_UNadj_constrained.tif",
    "CC BY 4.0",
    "b54a9a075af3d0964794af77d958d679aebbd01c4b2a340f3fdef0a287de981c",
    True,
)
META = Source(
    "Meta population map 2020",
    "mys_general_2020_geotiff.zip",
    "https://data.humdata.org/dataset/f165a732-7125-4321-baad-1b7005ed93d0/resource/e8e63524-9f06-486a-afd8-cbf752073d08/download/mys_general_2020_geotiff.zip",
    "CC BY",
    "31317c66c4d6506267c432cfa7161d3b2927b4adbf6760bad66931581da9250f",
    True,
)
FILE_SOURCES = (HEALTH, SCHOOLS, GTFS, DOSM, BOUNDARIES, WORLDPOP, META)
META_MEMBER = "mys_general_2020.tif"  # the one GeoTIFF inside the Meta zip, about 17.4 GB uncompressed

OSM_NAME = "OpenStreetMap"
OSM_LICENCE = "ODbL"
GEOFABRIK_DIR = "https://download.geofabrik.de/asia/"
GEOFABRIK_LATEST = GEOFABRIK_DIR + "malaysia-singapore-brunei-latest.osm.pbf"  # redirects to the dated file
GEOFABRIK_FILE = re.compile(r"^malaysia-singapore-brunei-(\d{2})(\d{2})(\d{2})\.osm\.pbf$")


@dataclass(frozen=True)
class Fetched:
    name: str
    url: str
    licence: str
    path: Path
    retrieved: str  # ISO 8601 timestamp, UTC
    bytes: int
    sha256: str


def download(url: str, path: Path) -> None:
    """Stream url to path through a partial file, so an interrupted download never looks complete."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response, partial.open("wb") as out:
        shutil.copyfileobj(response, out, 1 << 20)
    partial.replace(path)


def retrieved_at(path: Path) -> str:
    """When this cached file was downloaded, recorded beside it on first sight."""
    stamp = path.with_name(path.name + ".retrieved")
    if not stamp.exists():
        stamp.write_text(datetime.now(UTC).replace(microsecond=0).isoformat())
    return stamp.read_text().strip()


def fetch(source: Source, raw_dir: Path) -> Fetched:
    """Download once into raw_dir, then reuse the cache. A changed checksum stops the run for a fixed source."""
    path = raw_dir / source.file
    if not path.exists():
        log.info("downloading %s", source.name)
        download(source.url, path)
    digest = sha256_of(path)
    if digest != source.sha256:
        message = f"{source.name}: SHA-256 {digest} differs from {source.sha256}, checked on {CHECKED_ON}"
        if source.fixed:
            raise ValueError(message)
        log.warning(message)
    return Fetched(source.name, source.url, source.licence, path, retrieved_at(path), path.stat().st_size, digest)


def geofabrik_date(file_name: str) -> str:
    """The data date in a dated Geofabrik file name, as YYYY-MM-DD."""
    match = GEOFABRIK_FILE.match(file_name)
    if match is None:
        raise ValueError(f"{file_name!r} is not a dated malaysia-singapore-brunei .osm.pbf file")
    yy, mm, dd = match.groups()
    return f"20{yy}-{mm}-{dd}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def latest_geofabrik_url() -> str:
    """Ask Geofabrik which dated file `-latest` points at today, without downloading it."""
    request = urllib.request.Request(GEOFABRIK_LATEST, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=60) as response:
            return response.url
    except urllib.error.HTTPError as err:
        if err.code in (301, 302, 303, 307, 308):
            return str(err.headers["Location"])
        raise


def fetch_osm(raw_dir: Path) -> Fetched:
    """Reuse the newest cached dated extract, so a rerun uses the same roads; otherwise download today's."""
    cached = sorted(p for p in raw_dir.glob("malaysia-singapore-brunei-*.osm.pbf") if GEOFABRIK_FILE.match(p.name))
    if cached:
        path = cached[-1]
    else:
        url = latest_geofabrik_url()
        path = raw_dir / url.rsplit("/", 1)[-1]
        geofabrik_date(path.name)  # refuse anything that is not a dated extract
        log.info("downloading %s (about 250 MB)", path.name)
        download(url, path)
    return Fetched(OSM_NAME, GEOFABRIK_DIR + path.name, OSM_LICENCE, path, retrieved_at(path), path.stat().st_size, sha256_of(path))
```

Facility coordinates are checked against the districts' box widened by `AREA_MARGIN_DEG` (about 11 km): a clinic just across a boundary is kept and logged, as the spec says, but swapped or zero coordinates stop the run instead of drawing a point in the sea. `utf-8-sig` drops the byte order mark both state files start with.

Create `analysis/pulse/load.py`:

```python
"""Read the facility CSVs, the GTFS stops, the district outlines and the DOSM district totals."""

from __future__ import annotations

import csv
import datetime
import io
import json
import math
import re
import zipfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq
import shapely
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

Bounds = tuple[float, float, float, float]  # min lon, min lat, max lon, max lat


@dataclass(frozen=True)
class DistrictSpec:
    id: str
    name: str  # as spelled by both DOSM and geoBoundaries
    short: str
    land: str  # "island" or "mainland"


DISTRICTS = (
    DistrictSpec("tl", "Timur Laut", "Timur Laut", "island"),
    DistrictSpec("bd", "Barat Daya", "Barat Daya", "island"),
    DistrictSpec("spu", "Seberang Perai Utara", "SP Utara", "mainland"),
    DistrictSpec("spt", "Seberang Perai Tengah", "SP Tengah", "mainland"),
    DistrictSpec("sps", "Seberang Perai Selatan", "SP Selatan", "mainland"),
)
CATEGORIES = ("clinic", "school", "transit")
DENTAL = "KLINIK PERGIGIAN"
AREA_MARGIN_DEG = 0.1  # about 11 km: a facility further than this outside the districts' box has bad coordinates
DOSM_FILTER = {"state": "Pulau Pinang", "sex": "both", "age": "overall", "ethnicity": "overall"}
DOSM_DATE = datetime.date(2020, 1, 1)
DATE = re.compile(r"^\d{2}/\d{2}/(\d{4})$")


@dataclass(frozen=True)
class Facility:
    category: str
    lon: float
    lat: float
    year: int | None  # the record's TARIKH_DATA year; None for GTFS stops


def expand(bounds: Bounds, margin: float) -> Bounds:
    return (bounds[0] - margin, bounds[1] - margin, bounds[2] + margin, bounds[3] + margin)


def inside(bounds: Bounds, lon: float, lat: float) -> bool:
    return bounds[0] <= lon <= bounds[2] and bounds[1] <= lat <= bounds[3]


def read_rows(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    """CSV rows as dicts. utf-8-sig drops the byte order mark the state files start with, and is harmless without one."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name} is missing columns {missing}")
        return list(reader)


def parse_point(x: str, y: str, where: str) -> tuple[float, float]:
    """Longitude and latitude, failing on anything missing or non-numeric."""
    try:
        lon, lat = float(x), float(y)
    except ValueError:
        raise ValueError(f"{where}: bad coordinates X={x!r} Y={y!r}") from None
    if not (math.isfinite(lon) and math.isfinite(lat)):
        raise ValueError(f"{where}: bad coordinates X={x!r} Y={y!r}")
    return lon, lat


def data_year(value: str, where: str) -> int:
    match = DATE.match(value.strip())
    if match is None:
        raise ValueError(f"{where}: TARIKH_DATA {value!r} is not DD/MM/YYYY")
    return int(match.group(1))


def read_facilities(path: Path, category: str, area: Bounds, keep: Callable[[dict[str, str]], bool], extra: tuple[str, ...] = ()) -> list[Facility]:
    """Rows that pass keep, as facilities. A point outside area (for example X and Y swapped) is a bad coordinate."""
    facilities = []
    for line, row in enumerate(read_rows(path, ("X", "Y", "TARIKH_DATA", *extra)), start=2):  # line 1 is the header
        if not keep(row):
            continue
        where = f"{path.name} line {line}"
        lon, lat = parse_point(row["X"], row["Y"], where)
        if not inside(area, lon, lat):
            raise ValueError(f"{where}: coordinates X={row['X']!r} Y={row['Y']!r} are not in the Penang area")
        facilities.append(Facility(category, lon, lat, data_year(row["TARIKH_DATA"], where)))
    return facilities


def read_clinics(path: Path, area: Bounds) -> list[Facility]:
    """Every public health facility except dental clinics."""
    return read_facilities(path, "clinic", area, lambda row: row["JENIS"] != DENTAL, extra=("JENIS",))


def read_schools(path: Path, area: Bounds) -> list[Facility]:
    """Every school, private ones included."""
    return read_facilities(path, "school", area, lambda row: True)


def read_stops(gtfs_zip: Path, land: BaseGeometry) -> list[Facility]:
    """Rapid Penang stops inside the five districts. Stops elsewhere on the network are left out."""
    with zipfile.ZipFile(gtfs_zip) as archive, archive.open("stops.txt") as raw:
        rows = list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig")))
    points = [parse_point(r["stop_lon"], r["stop_lat"], f"stops.txt line {i}") for i, r in enumerate(rows, start=2)]
    return [Facility("transit", lon, lat, None) for lon, lat in points if shapely.contains_xy(land, lon, lat)]


def load_districts(path: Path) -> list[BaseGeometry]:
    """The five district outlines from geoBoundaries ADM2, in DISTRICTS order, selected by name."""
    features = json.loads(path.read_text())["features"]
    found = {f["properties"]["shapeName"]: shape(f["geometry"]) for f in features}
    missing = [d.name for d in DISTRICTS if d.name not in found]
    if missing:
        raise ValueError(f"{path.name} has no district named {missing}")
    return [found[d.name] for d in DISTRICTS]


def load_totals(path: Path) -> list[int]:
    """DOSM 2020 population per district, in people, in DISTRICTS order. The file stores thousands."""
    condition = pc.field("date") == DOSM_DATE
    for column, value in DOSM_FILTER.items():
        condition = condition & (pc.field(column) == value)
    rows = pq.read_table(path, columns=["district", "population"], filters=condition).to_pylist()
    totals: dict[str, int] = {}
    for row in rows:
        if row["district"] in totals:
            raise ValueError(f"{path.name} has more than one 2020 total for {row['district']}")
        totals[row["district"]] = round(row["population"] * 1000)
    missing = [d.name for d in DISTRICTS if d.name not in totals]
    if missing:
        raise ValueError(f"{path.name} has no 2020 total for {missing}")
    return [totals[d.name] for d in DISTRICTS]


def outside_districts(facilities: list[Facility], land: BaseGeometry) -> dict[str, int]:
    """How many facilities of each category lie outside every district. They are kept, and logged by the caller."""
    counts = Counter(f.category for f in facilities if not shapely.contains_xy(land, f.lon, f.lat))
    return {c: counts[c] for c in CATEGORIES}
```

- [ ] **Step 5: Run the tests**

Run (in `analysis/`): `uv run pytest tests/pulse`, then `uv run pytest`.
Expected: `21 passed`, then `77 passed`.

- [ ] **Step 6: Commit**

```bash
git add analysis/pyproject.toml \
  analysis/uv.lock \
  analysis/pulse/__init__.py \
  analysis/pulse/sources.py \
  analysis/pulse/load.py \
  analysis/tests/pulse/__init__.py \
  analysis/tests/pulse/world.py \
  analysis/tests/pulse/test_sources.py \
  analysis/tests/pulse/test_load.py
git commit -m "feat: add Penang Pulse sources and loaders"
```

---

### Task 4: Python: the population surface

**Files:**
- Create: `analysis/pulse/population.py`
- Modify: `analysis/tests/pulse/world.py` (raster writers)
- Test: `analysis/tests/pulse/test_population.py`

**Interfaces:**
- Consumes: `DISTRICTS`, `Bounds`, `load_districts`, `load_totals` (`pulse.load`, Task 3); `META_MEMBER` (`pulse.sources`, Task 3); `write_boundaries`, `write_dosm`, `BOXES` (`tests/pulse/world.py`, Task 3).
- Produces, in `pulse.population`: `Cells(lon, lat, people, district)` (numpy arrays; `district` indexes `DISTRICTS`); `meta_path(zip_path: Path) -> str` (`/vsizip/<zip>/mys_general_2020.tif`); `window_for(src, bounds) -> Window`; `read_populated(raster: str, bounds) -> tuple[lon, lat, value]`; `read_cells(raster: str, districts: Sequence[BaseGeometry], totals: Sequence[int]) -> Cells`, which raises `ValueError("<district> has no populated cells in <raster>")`.
- Produces, in `tests/pulse/world.py`: `GRID_ORIGIN`, `GRID_STEP`, `LAND_COLUMNS`, `NODATA_CELL`, `population_grid(value, nodata)`, `write_raster(path, grid, dtype, nodata)`, `write_worldpop(folder) -> Path` (float32, nodata -99999), `write_meta(folder) -> Path` (a zip holding a float64 GeoTIFF with NaN nodata under `META_MEMBER`).

Checked on the real files on 2026-10-14: the WorldPop window for Penang is 452 by 556 cells (0.1 s), the Meta window through `/vsizip/` is 1,353 by 1,666 cells (2.8 s, never extracted), and rescaling hits the DOSM totals exactly (556,600; 237,700; 339,100; 423,000; 184,000).

- [ ] **Step 1: Write the failing test**

In `analysis/tests/pulse/world.py`, replace the import block:

```python
from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import MultiPolygon, box, mapping
```

with:

```python
from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import MultiPolygon, box, mapping

from pulse.sources import META_MEMBER
```

Append to `analysis/tests/pulse/world.py`:

```python
GRID_ORIGIN = (100.20, 5.36)  # top left corner of the population grid
GRID_STEP = 0.01  # degrees per cell, so cell centres sit at 100.205, 100.215, ...
LAND_COLUMNS = (0, 1, 3, 4, 5)  # column 2 is the strait
NODATA_CELL = (0, 0)  # one Timur Laut cell with no data


def population_grid(value: float, nodata: float) -> np.ndarray:
    grid = np.zeros((6, 6))
    grid[:, list(LAND_COLUMNS)] = value
    grid[NODATA_CELL] = nodata
    return grid


def write_raster(path: Path, grid: np.ndarray, dtype: str, nodata: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    transform = from_origin(*GRID_ORIGIN, GRID_STEP, GRID_STEP)
    with rasterio.open(path, "w", driver="GTiff", width=6, height=6, count=1, dtype=dtype, crs="EPSG:4326", transform=transform, nodata=nodata) as dst:
        dst.write(grid.astype(dtype), 1)
    return path


def write_worldpop(folder: Path) -> Path:
    """WorldPop style: float32 with -99999 for nodata."""
    return write_raster(folder / "worldpop.tif", population_grid(10.0, -99999.0), "float32", -99999.0)


def write_meta(folder: Path) -> Path:
    """Meta style: a float64 GeoTIFF with NaN for nodata, zipped under the real member name."""
    tif = write_raster(folder / "meta.tif", population_grid(20.0, np.nan), "float64", np.nan)
    path = folder / "meta.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(tif, META_MEMBER)
    tif.unlink()
    return path
```

Create `analysis/tests/pulse/test_population.py`:

```python
from pathlib import Path

import numpy as np
import pytest
import rasterio
from shapely.geometry import box

from pulse.load import load_districts, load_totals
from pulse.population import meta_path, read_cells, window_for

from .world import BOXES, write_boundaries, write_dosm, write_meta, write_worldpop


@pytest.fixture
def districts(tmp_path: Path) -> list:
    return load_districts(write_boundaries(tmp_path))


@pytest.fixture
def totals(tmp_path: Path) -> list[int]:
    return load_totals(write_dosm(tmp_path))


def test_cells_are_assigned_to_the_district_holding_their_centre(tmp_path: Path, districts: list, totals: list[int]) -> None:
    cells = read_cells(str(write_worldpop(tmp_path)), districts, totals)
    # 6 cells per district on the 6 by 6 grid, less the one nodata cell in Timur Laut; the strait column holds nobody.
    assert np.bincount(cells.district).tolist() == [5, 6, 6, 6, 6]
    for i, (west, south, east, north) in enumerate(BOXES.values()):
        mine = cells.district == i
        assert ((cells.lon[mine] > west) & (cells.lon[mine] < east) & (cells.lat[mine] > south) & (cells.lat[mine] < north)).all()


def test_each_district_is_rescaled_to_its_dosm_total(tmp_path: Path, districts: list, totals: list[int]) -> None:
    cells = read_cells(str(write_worldpop(tmp_path)), districts, totals)
    sums = np.bincount(cells.district, weights=cells.people)
    assert sums == pytest.approx(totals, rel=1e-12)


def test_the_meta_raster_is_read_inside_its_zip_and_nan_is_nobody(tmp_path: Path, districts: list, totals: list[int]) -> None:
    cells = read_cells(meta_path(write_meta(tmp_path)), districts, totals)
    assert np.bincount(cells.district).tolist() == [5, 6, 6, 6, 6]
    assert np.isfinite(cells.people).all()
    assert np.bincount(cells.district, weights=cells.people) == pytest.approx(totals, rel=1e-12)


def test_a_district_without_populated_cells_stops_the_run(tmp_path: Path, districts: list, totals: list[int]) -> None:
    in_the_strait = box(100.2205, 5.3005, 100.2295, 5.3195)  # holds no populated cell centre
    with pytest.raises(ValueError, match="Seberang Perai Selatan has no populated cells"):
        read_cells(str(write_worldpop(tmp_path)), [*districts[:4], in_the_strait], totals)


def test_the_window_covers_whole_cells_and_stays_on_the_raster(tmp_path: Path) -> None:
    with rasterio.open(write_worldpop(tmp_path)) as src:
        assert window_for(src, (100.205, 5.315, 100.235, 5.355)).flatten() == (0, 0, 4, 5)
        assert window_for(src, (100.0, 5.0, 101.0, 6.0)).flatten() == (0, 0, 6, 6)
```

- [ ] **Step 2: Run the test to verify it fails**

Run (in `analysis/`): `uv run pytest tests/pulse/test_population.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse.population'`.

- [ ] **Step 3: Write the population surface**

Create `analysis/pulse/population.py`:

```python
"""Residents per populated grid cell: read a population raster over Penang, assign cells to districts, rescale to DOSM totals."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
import shapely
from rasterio.transform import xy
from rasterio.windows import Window, from_bounds
from shapely.geometry.base import BaseGeometry

from .load import DISTRICTS, Bounds
from .sources import META_MEMBER


@dataclass(frozen=True)
class Cells:
    lon: np.ndarray  # cell centres
    lat: np.ndarray
    people: np.ndarray  # residents, after rescaling to the district totals
    district: np.ndarray  # index into DISTRICTS


def meta_path(zip_path: Path) -> str:
    """GDAL path that reads the Meta GeoTIFF inside its zip in place, so the 17.4 GB file is never extracted."""
    return f"/vsizip/{zip_path}/{META_MEMBER}"


def window_for(src: rasterio.DatasetReader, bounds: Bounds) -> Window:
    """Whole-cell window covering bounds, clipped to the raster."""
    w = from_bounds(*bounds, transform=src.transform)
    col0, row0 = math.floor(w.col_off), math.floor(w.row_off)
    col1, row1 = math.ceil(w.col_off + w.width), math.ceil(w.row_off + w.height)
    return Window(col0, row0, col1 - col0, row1 - row0).intersection(Window(0, 0, src.width, src.height))


def read_populated(raster: str, bounds: Bounds) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Centre lon, centre lat and value of every cell above zero in the window. Nodata, including NaN, counts as zero."""
    with rasterio.open(raster) as src:
        window = window_for(src, bounds)
        values = np.nan_to_num(src.read(1, window=window, masked=True).astype(np.float64).filled(0.0), nan=0.0)
        transform = src.window_transform(window)
    rows, cols = np.nonzero(values > 0)
    lon, lat = xy(transform, rows, cols, offset="center")
    return np.asarray(lon, dtype=np.float64), np.asarray(lat, dtype=np.float64), values[rows, cols]


def read_cells(raster: str, districts: Sequence[BaseGeometry], totals: Sequence[int]) -> Cells:
    """Populated cells whose centre lies in a district, each district rescaled so its cells sum to its DOSM total."""
    lon, lat, values = read_populated(raster, shapely.union_all(list(districts)).bounds)
    district = np.full(len(values), -1)
    for i, geom in enumerate(districts):
        district[(district == -1) & shapely.contains_xy(geom, lon, lat)] = i
    keep = district >= 0
    lon, lat, values, district = lon[keep], lat[keep], values[keep], district[keep]
    people = np.zeros(len(values))
    for i, total in enumerate(totals):
        mask = district == i
        if not mask.any():
            raise ValueError(f"{DISTRICTS[i].name} has no populated cells in {raster}")
        people[mask] = values[mask] * (total / values[mask].sum())
    return Cells(lon=lon, lat=lat, people=people, district=district)
```

- [ ] **Step 4: Run the tests**

Run (in `analysis/`): `uv run pytest tests/pulse/test_population.py`, then `uv run pytest`.
Expected: `5 passed`, then `82 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/pulse/population.py \
  analysis/tests/pulse/world.py \
  analysis/tests/pulse/test_population.py
git commit -m "feat: build the Penang Pulse population surface"
```

---

### Task 5: Python: the road graph, bridges and towns from OpenStreetMap

**Files:**
- Create: `analysis/pulse/roads.py`
- Modify: `analysis/tests/pulse/world.py` (an `.osm` writer)
- Test: `analysis/tests/pulse/test_roads.py`

**Interfaces:**
- Consumes: `Bounds` (`pulse.load`, Task 3).
- Produces, in `pulse.roads`: `EARTH_RADIUS_M`, `ROAD_TYPES`, `BLOCKED_ACCESS`, `PLACE_RANK`, `BRIDGES` (map name to OSM name variants), `PLACES` (the six town labels, in the fixture's order), `TAG_FILTER`; `Way(names, nodes)`; `Place(name, rank, osm_id, lon, lat)`; `Roads(graph, dropped, bridges, places)` where `graph` is the largest connected component as an undirected `nx.Graph` with node attributes `lon` and `lat` and edge attribute `weight` in metres, `bridges: dict[str, list[list[tuple[float, float]]]]` and `places: dict[str, tuple[float, float]]` (lon, lat); `haversine(lon1, lat1, lon2, lat2) -> float`; `road_way(obj, bbox) -> Way | None`; `place_node(obj, bbox) -> Place | None`; `build_graph(ways) -> tuple[nx.Graph, int]`; `find_bridges(ways)`; `pick_places(candidates)`; `read_osm(path: Path, bbox: Bounds) -> Roads`.
- Produces, in `tests/pulse/world.py`: `OSM_NODES`, `OSM_WAYS`, `OSM_PLACES`, `OSM_BBOX`, `tag_xml(tags)`, `write_osm(folder, ways=OSM_WAYS, places=OSM_PLACES) -> Path`.

Names checked against OpenStreetMap on 2026-10-14 (Overpass and Nominatim): the first bridge's ways are `name=Jambatan Pulau Pinang`, `name:en=Penang Bridge`; the second's are `name=Jambatan Sultan Abdul Halim Mu'adzam Shah`, `name:en=Sultan Abdul Halim Mu'adzam Shah Bridge` (with an apostrophe; both are `highway=motorway`). The six towns are place nodes whose `name` is exactly `George Town` (city), `Butterworth` (city), `Bukit Mertajam` (city), `Bayan Lepas` (town), `Balik Pulau` (town) and `Nibong Tebal` (town); neighbourhoods such as `Zon Perindustrian Bebas Bayan Lepas Fasa IV` do not match exactly. The lookup matches `name` or `name:en` against a list of variants and fails with the names it looked for.

pyosmium 4.3.1's `FileProcessor(...).with_locations().with_filter(TagFilter(...))` was checked on an `.osm` file and on the same data written as `.osm.pbf`: node locations are filled before the filter drops untagged nodes, so ways keep their coordinates and Python only sees road ways and place nodes.

- [ ] **Step 1: Write the failing test**

In `analysis/tests/pulse/world.py`, replace the import block:

```python
from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import MultiPolygon, box, mapping

from pulse.sources import META_MEMBER
```

with:

```python
from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import MultiPolygon, box, mapping

from pulse.sources import META_MEMBER
```

Append to `analysis/tests/pulse/world.py`:

```python
OSM_NODES = {  # id: (lon, lat)
    **{i: (100.21, 5.295 + 0.01 * i) for i in range(1, 7)},  # island street, 5.305 to 5.355
    **{10 + i: (100.245, 5.295 + 0.01 * i) for i in range(1, 7)},  # mainland street
    21: (100.2275, 5.335),  # mid-strait point of the Penang Bridge
    22: (100.2275, 5.305),  # mid-strait point of the second bridge
    31: (100.255, 5.355), 32: (100.256, 5.355),  # a fragment joined to nothing
    51: (101.50, 5.50), 52: (101.51, 5.50),  # a road far outside the Penang box
    41: (100.21, 5.355), 42: (100.21, 5.305), 43: (100.205, 5.32), 44: (100.24, 5.355), 45: (100.255, 5.33), 46: (100.25, 5.305),
    47: (100.215, 5.31),  # a neighbourhood that shares the name Bayan Lepas
}
OSM_WAYS = [  # id, node ids, tags
    (101, [1, 2, 3, 4, 5, 6], {"highway": "residential", "name": "Jalan Pulau"}),
    (102, [11, 12, 13, 14, 15, 16], {"highway": "primary", "name": "Jalan Tanah Besar"}),
    (103, [4, 21, 14], {"highway": "motorway", "bridge": "yes", "name": "Jambatan Pulau Pinang", "name:en": "Penang Bridge"}),
    (104, [1, 22, 11], {"highway": "motorway", "bridge": "yes", "name": "Jambatan Sultan Abdul Halim Mu'adzam Shah"}),
    (105, [6, 16], {"highway": "footway"}),  # footpaths are not roads
    (106, [5, 15], {"highway": "service", "access": "private"}),  # neither are private roads
    (107, [3, 13], {"route": "ferry"}),  # nor ferries
    (108, [31, 32], {"highway": "residential"}),
    (109, [51, 52], {"highway": "residential"}),
]
OSM_PLACES = {  # node id: tags
    41: {"place": "city", "name": "George Town"},
    42: {"place": "town", "name": "Bayan Lepas"},
    43: {"place": "town", "name": "Balik Pulau"},
    44: {"place": "city", "name": "Butterworth"},
    45: {"place": "city", "name": "Bukit Mertajam"},
    46: {"place": "town", "name": "Nibong Tebal"},
    47: {"place": "neighbourhood", "name": "Bayan Lepas"},
}
OSM_BBOX = (100.15, 5.25, 100.31, 5.41)  # the districts' box widened by ROAD_MARGIN_DEG


def tag_xml(tags: dict[str, str]) -> str:
    return "".join(f"<tag k={quoteattr(k)} v={quoteattr(v)}/>" for k, v in tags.items())


def write_osm(folder: Path, ways: list[tuple[int, list[int], dict[str, str]]] = OSM_WAYS, places: dict[int, dict[str, str]] = OSM_PLACES) -> Path:
    """An .osm XML file. pyosmium reads it exactly as it reads the real .osm.pbf."""
    nodes = [f'<node id="{i}" version="1" lat="{lat}" lon="{lon}">{tag_xml(places.get(i, {}))}</node>' for i, (lon, lat) in OSM_NODES.items()]
    way_xml = [f'<way id="{i}" version="1">' + "".join(f'<nd ref="{n}"/>' for n in refs) + f"{tag_xml(tags)}</way>" for i, refs, tags in ways]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "penang.osm"
    path.write_text("<?xml version='1.0' encoding='UTF-8'?>\n<osm version=\"0.6\">\n" + "\n".join([*nodes, *way_xml]) + "\n</osm>\n")
    return path
```

Create `analysis/tests/pulse/test_roads.py`:

```python
from pathlib import Path

import networkx as nx
import pytest

from pulse.roads import PLACES, haversine, read_osm

from .world import OSM_BBOX, OSM_PLACES, OSM_WAYS, write_osm


def test_the_graph_keeps_roads_and_drops_paths_ferries_private_roads_and_fragments(tmp_path: Path) -> None:
    roads = read_osm(write_osm(tmp_path), OSM_BBOX)
    assert sorted(roads.graph.nodes) == [1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16, 21, 22]
    assert roads.dropped == 2  # the two-node fragment
    assert not roads.graph.has_edge(6, 16) and not roads.graph.has_edge(5, 15) and not roads.graph.has_edge(3, 13)
    assert roads.graph.nodes[21] == {"lon": 100.2275, "lat": 5.335}


def test_edges_weigh_their_length_in_metres(tmp_path: Path) -> None:
    graph = read_osm(write_osm(tmp_path), OSM_BBOX).graph
    assert graph.edges[1, 2]["weight"] == pytest.approx(haversine(100.21, 5.305, 100.21, 5.315))
    assert graph.edges[1, 2]["weight"] == pytest.approx(1112, abs=1)  # 0.01 degrees of latitude
    assert nx.shortest_path(graph, 3, 13, weight="weight") == [3, 4, 21, 14, 13]  # over the Penang Bridge, not the ferry


def test_both_bridges_and_all_six_places_are_found(tmp_path: Path) -> None:
    roads = read_osm(write_osm(tmp_path), OSM_BBOX)
    assert roads.bridges == {
        "Penang Bridge": [[(100.21, 5.335), (100.2275, 5.335), (100.245, 5.335)]],
        "Sultan Abdul Halim Muadzam Shah Bridge": [[(100.21, 5.305), (100.2275, 5.305), (100.245, 5.305)]],
    }
    assert list(roads.places) == list(PLACES)
    assert roads.places["George Town"] == (100.21, 5.355)


def test_a_town_beats_a_neighbourhood_with_the_same_name(tmp_path: Path) -> None:
    assert read_osm(write_osm(tmp_path), OSM_BBOX).places["Bayan Lepas"] == (100.21, 5.305)


def test_a_missing_bridge_stops_the_run(tmp_path: Path) -> None:
    ways = [w for w in OSM_WAYS if w[0] != 104]
    with pytest.raises(ValueError, match="no road named .*Sultan Abdul Halim"):
        read_osm(write_osm(tmp_path, ways=ways), OSM_BBOX)


def test_a_missing_place_stops_the_run(tmp_path: Path) -> None:
    places = {k: v for k, v in OSM_PLACES.items() if v["name"] != "Nibong Tebal"}
    with pytest.raises(ValueError, match=r"no place node named \['Nibong Tebal'\]"):
        read_osm(write_osm(tmp_path, places=places), OSM_BBOX)
```

- [ ] **Step 2: Run the test to verify it fails**

Run (in `analysis/`): `uv run pytest tests/pulse/test_roads.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse.roads'`.

- [ ] **Step 3: Write the reader**

Create `analysis/pulse/roads.py`:

```python
"""Read the Geofabrik extract: the drivable road graph around Penang, the two bridges and six town labels."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import osmium

from .load import Bounds

log = logging.getLogger(__name__)

EARTH_RADIUS_M = 6_371_008.8
MAIN_ROADS = ("motorway", "trunk", "primary", "secondary", "tertiary")
ROAD_TYPES = (*MAIN_ROADS, *(f"{r}_link" for r in MAIN_ROADS), "unclassified", "residential", "living_street", "service", "road")
BLOCKED_ACCESS = ("private", "no")
PLACE_RANK = ("city", "town", "suburb", "village", "hamlet", "neighbourhood", "quarter", "locality")  # best first
BRIDGES = {  # the name shown on the map: the OSM `name` or `name:en` values that identify its ways
    "Penang Bridge": ("Jambatan Pulau Pinang", "Penang Bridge"),
    "Sultan Abdul Halim Muadzam Shah Bridge": (
        "Jambatan Sultan Abdul Halim Mu'adzam Shah",
        "Sultan Abdul Halim Mu'adzam Shah Bridge",
        "Jambatan Sultan Abdul Halim Muadzam Shah",
        "Sultan Abdul Halim Muadzam Shah Bridge",
    ),
}
PLACES = ("George Town", "Bayan Lepas", "Balik Pulau", "Butterworth", "Bukit Mertajam", "Nibong Tebal")
TAG_FILTER = osmium.filter.TagFilter(*(("highway", r) for r in ROAD_TYPES), *(("place", p) for p in PLACE_RANK))

Point = tuple[float, float]  # lon, lat


@dataclass(frozen=True)
class Way:
    names: frozenset[str]  # its `name` and `name:en`
    nodes: tuple[tuple[int, float, float], ...]  # OSM node id, lon, lat


@dataclass(frozen=True)
class Place:
    name: str
    rank: int  # index in PLACE_RANK
    osm_id: int
    lon: float
    lat: float


@dataclass(frozen=True)
class Roads:
    graph: nx.Graph  # largest connected component; nodes are OSM ids with lon and lat attributes, edges weigh metres
    dropped: int  # nodes outside the largest component
    bridges: dict[str, list[list[Point]]]  # each bridge's ways as lon, lat lines
    places: dict[str, Point]


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def inside(bbox: Bounds, lon: float, lat: float) -> bool:
    return bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]


def road_way(obj: osmium.osm.Way, bbox: Bounds) -> Way | None:
    """A drivable way with at least one node in bbox. Footpaths, ferries and private or closed roads are not roads here."""
    tags = obj.tags
    if tags.get("highway") not in ROAD_TYPES or tags.get("access") in BLOCKED_ACCESS or tags.get("route") == "ferry" or "ferry" in tags:
        return None
    nodes = tuple((n.ref, n.lon, n.lat) for n in obj.nodes if n.location.valid())
    if len(nodes) < 2 or not any(inside(bbox, lon, lat) for _, lon, lat in nodes):
        return None
    return Way(frozenset(v for k in ("name", "name:en") if (v := tags.get(k))), nodes)


def place_node(obj: osmium.osm.Node, bbox: Bounds) -> Place | None:
    """A place node in bbox whose `name` or `name:en` is one of PLACES."""
    tags = obj.tags
    kind = tags.get("place")
    if kind not in PLACE_RANK or not inside(bbox, obj.location.lon, obj.location.lat):
        return None
    name = next((n for n in (tags.get("name"), tags.get("name:en")) if n in PLACES), None)
    return None if name is None else Place(name, PLACE_RANK.index(kind), obj.id, obj.location.lon, obj.location.lat)


def build_graph(ways: list[Way]) -> tuple[nx.Graph, int]:
    """Undirected graph over every way, cut to its largest connected component. Returns the graph and how many nodes were dropped."""
    graph = nx.Graph()
    for way in ways:
        for (a, lon_a, lat_a), (b, lon_b, lat_b) in zip(way.nodes, way.nodes[1:], strict=False):
            graph.add_node(a, lon=lon_a, lat=lat_a)
            graph.add_node(b, lon=lon_b, lat=lat_b)
            graph.add_edge(a, b, weight=haversine(lon_a, lat_a, lon_b, lat_b))
    largest = max(nx.connected_components(graph), key=len)
    return graph.subgraph(largest).copy(), graph.number_of_nodes() - len(largest)


def find_bridges(ways: list[Way]) -> dict[str, list[list[Point]]]:
    found = {name: [[(lon, lat) for _, lon, lat in w.nodes] for w in ways if w.names & set(variants)] for name, variants in BRIDGES.items()}
    missing = [name for name, lines in found.items() if not lines]
    if missing:
        raise ValueError(f"OpenStreetMap has no road named {[BRIDGES[m] for m in missing]} near Penang")
    return found


def pick_places(candidates: list[Place]) -> dict[str, Point]:
    """For each name, the highest ranked place node (a town beats a neighbourhood of the same name), then the lowest OSM id."""
    best: dict[str, Place] = {}
    for place in sorted(candidates, key=lambda p: (p.rank, p.osm_id)):
        best.setdefault(place.name, place)
    missing = [name for name in PLACES if name not in best]
    if missing:
        raise ValueError(f"OpenStreetMap has no place node named {missing} near Penang")
    return {name: (best[name].lon, best[name].lat) for name in PLACES}


def read_osm(path: Path, bbox: Bounds) -> Roads:
    ways: list[Way] = []
    places: list[Place] = []
    for obj in osmium.FileProcessor(str(path)).with_locations().with_filter(TAG_FILTER):
        if obj.is_way() and (way := road_way(obj, bbox)) is not None:
            ways.append(way)
        elif obj.is_node() and (place := place_node(obj, bbox)) is not None:
            places.append(place)
    log.info("read %d road ways and %d place nodes", len(ways), len(places))
    graph, dropped = build_graph(ways)
    log.info("road graph: %d nodes, %d edges; %d nodes outside the largest component dropped", graph.number_of_nodes(), graph.number_of_edges(), dropped)
    return Roads(graph=graph, dropped=dropped, bridges=find_bridges(ways), places=pick_places(places))
```

- [ ] **Step 4: Run the tests**

Run (in `analysis/`): `uv run pytest tests/pulse/test_roads.py`, then `uv run pytest`.
Expected: `6 passed`, then `88 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/pulse/roads.py \
  analysis/tests/pulse/world.py \
  analysis/tests/pulse/test_roads.py
git commit -m "feat: read the Penang road graph, bridges and towns from OpenStreetMap"
```

---

### Task 6: Python: snapping, multi-source road distance and bands

**Files:**
- Create: `analysis/pulse/distance.py`
- Test: `analysis/tests/pulse/test_distance.py`

**Interfaces:**
- Consumes: a graph shaped like `Roads.graph` and `haversine` (`pulse.roads`, Task 5).
- Produces, in `pulse.distance`: `LON0`, `LAT0`, `EARTH_RADIUS_M`, `BAND_EDGES_M = (1000.0, 3000.0)`, `SOURCE`; `to_metres(lon, lat) -> tuple[ndarray, ndarray]`; `RoadIndex(nodes, tree)`; `Snap(node, metres)`; `road_index(graph) -> RoadIndex`; `snap(index, lon, lat) -> Snap`; `network_from(graph, facilities: Snap) -> dict[object, float]` (road distance from every node to the nearest facility, including that facility's snap); `cell_distances(lengths, cells: Snap) -> ndarray` (raises `RuntimeError` if a cell's node has no route); `band_shares(distance, people, district, districts) -> ndarray` of shape (districts, 3), in percent; `largest_remainder(shares, total=100) -> tuple[int, ...]`.

A cell's distance is its straight line to the nearest road node, plus the network distance from that node to the nearest facility's road node, plus that facility's straight line to its node. One Dijkstra per category from a virtual source joined to each facility's node by its snap length gives the network part for every node at once. The graph is copied before the virtual source is added, so the shared road graph is never changed.

- [ ] **Step 1: Write the failing test**

Create `analysis/tests/pulse/test_distance.py`:

```python
import networkx as nx
import numpy as np
import pytest

from pulse.distance import band_shares, cell_distances, largest_remainder, network_from, road_index, snap, to_metres
from pulse.roads import haversine


def line_graph(points: dict[int, tuple[float, float]], edges: list[tuple[int, int]]) -> nx.Graph:
    graph = nx.Graph()
    for n, (lon, lat) in points.items():
        graph.add_node(n, lon=lon, lat=lat)
    for a, b in edges:
        graph.add_edge(a, b, weight=haversine(*points[a], *points[b]))
    return graph


# An island road (1-2), a bridge (2-3) and a mainland road (3-4), each about 1.1 km.
STRAIT = {1: (100.21, 5.30), 2: (100.22, 5.30), 3: (100.23, 5.30), 4: (100.24, 5.30)}


def metres_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    (xa, ya), (xb, yb) = to_metres(*map(np.array, a)), to_metres(*map(np.array, b))
    return float(np.hypot(xa - xb, ya - yb))


def test_distance_is_cell_snap_plus_network_plus_facility_snap() -> None:
    graph = line_graph(STRAIT, [(1, 2), (2, 3), (3, 4)])
    index = road_index(graph)
    facility, cell = (100.24, 5.302), (100.21, 5.299)  # just off nodes 4 and 1
    lengths = network_from(graph, snap(index, np.array([facility[0]]), np.array([facility[1]])))
    got = cell_distances(lengths, snap(index, np.array([cell[0]]), np.array([cell[1]])))
    network = sum(graph.edges[e]["weight"] for e in [(1, 2), (2, 3), (3, 4)])
    assert got[0] == pytest.approx(metres_between(cell, STRAIT[1]) + network + metres_between(facility, STRAIT[4]))


def test_a_facility_across_the_strait_is_reached_only_over_the_bridge() -> None:
    points = {**STRAIT, 5: (100.21, 5.31), 6: (100.24, 5.31)}  # a second pair of shore nodes with no bridge between them
    graph = line_graph(points, [(1, 2), (2, 3), (3, 4), (1, 5), (4, 6)])
    index = road_index(graph)
    lengths = network_from(graph, snap(index, np.array([100.24]), np.array([5.31])))  # facility at node 6
    over_bridge = sum(graph.edges[e]["weight"] for e in [(5, 1), (1, 2), (2, 3), (3, 4), (4, 6)])
    assert lengths[5] == pytest.approx(over_bridge)
    assert lengths[5] > metres_between(points[5], points[6]) + 2000  # well beyond the straight line across the water


def test_the_nearest_of_several_facilities_wins() -> None:
    graph = line_graph(STRAIT, [(1, 2), (2, 3), (3, 4)])
    lengths = network_from(graph, snap(road_index(graph), np.array([100.21, 100.24]), np.array([5.30, 5.30])))
    assert lengths[2] == pytest.approx(graph.edges[1, 2]["weight"])
    assert lengths[3] == pytest.approx(graph.edges[3, 4]["weight"])


def test_a_facility_beside_a_dropped_fragment_snaps_to_the_main_network() -> None:
    # The graph passed in is already the largest component, so the fragment's nodes are not there to snap to.
    main = line_graph(STRAIT, [(1, 2), (2, 3), (3, 4)])
    beside_fragment = (100.2405, 5.3105)  # the fragment sat at 100.24, 5.31; node 4 is about 1.2 km south
    snapped = snap(road_index(main), np.array([beside_fragment[0]]), np.array([beside_fragment[1]]))
    assert snapped.node.tolist() == [4]
    lengths = network_from(main, snapped)
    assert lengths[4] == pytest.approx(metres_between(beside_fragment, STRAIT[4]))


def test_an_unreachable_cell_is_a_bug_not_a_number() -> None:
    graph = line_graph({**STRAIT, 9: (100.30, 5.40)}, [(1, 2), (2, 3), (3, 4)])
    index = road_index(graph)
    lengths = network_from(graph, snap(index, np.array([100.21]), np.array([5.30])))
    with pytest.raises(RuntimeError, match="no route to any facility"):
        cell_distances(lengths, snap(index, np.array([100.30]), np.array([5.40])))


def test_band_shares_weigh_residents_and_put_the_edges_in_the_lower_band() -> None:
    distance = np.array([999.0, 1000.0, 3000.0, 3000.1, 50.0])
    people = np.array([1.0, 1.0, 1.0, 1.0, 4.0])
    district = np.array([0, 0, 0, 0, 1])
    shares = band_shares(distance, people, district, 2)
    assert shares.tolist() == [[25.0, 50.0, 25.0], [100.0, 0.0, 0.0]]


@pytest.mark.parametrize(
    ("shares", "rounded"),
    [([33.4, 33.3, 33.3], (34, 33, 33)), ([33.3333, 33.3333, 33.3334], (33, 33, 34)), ([0.4, 0.4, 99.2], (1, 0, 99)), ([72.5, 24.5, 3.0], (73, 24, 3)), ([100.0, 0.0, 0.0], (100, 0, 0))],
)
def test_largest_remainder_rounding_sums_to_100(shares: list[float], rounded: tuple[int, ...]) -> None:
    assert largest_remainder(shares) == rounded
    assert sum(largest_remainder(shares)) == 100
```

- [ ] **Step 2: Run the test to verify it fails**

Run (in `analysis/`): `uv run pytest tests/pulse/test_distance.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse.distance'`.

- [ ] **Step 3: Write the distances**

Create `analysis/pulse/distance.py`:

```python
"""Road distance from each populated cell to the nearest facility, and the share of residents in each distance band."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

LON0, LAT0 = 100.35, 5.35  # Penang's centre, for a local equirectangular projection in metres
EARTH_RADIUS_M = 6_371_008.8
BAND_EDGES_M = (1000.0, 3000.0)  # under 1 km, 1 to 3 km, over 3 km
SOURCE = "facilities"  # the virtual node joined to every facility's road node


def to_metres(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Metres east and north of Penang's centre. The error is well under 0.1% across Penang."""
    k = EARTH_RADIUS_M * math.pi / 180
    return (np.asarray(lon) - LON0) * k * math.cos(math.radians(LAT0)), (np.asarray(lat) - LAT0) * k


@dataclass(frozen=True)
class RoadIndex:
    nodes: np.ndarray  # graph node ids, in tree order
    tree: cKDTree  # over node positions in metres


@dataclass(frozen=True)
class Snap:
    node: np.ndarray  # nearest road node for each point
    metres: np.ndarray  # straight line from the point to that node


def road_index(graph: nx.Graph) -> RoadIndex:
    nodes = np.array(list(graph.nodes))
    x, y = to_metres(np.array([graph.nodes[n]["lon"] for n in nodes]), np.array([graph.nodes[n]["lat"] for n in nodes]))
    return RoadIndex(nodes=nodes, tree=cKDTree(np.column_stack([x, y])))


def snap(index: RoadIndex, lon: np.ndarray, lat: np.ndarray) -> Snap:
    x, y = to_metres(lon, lat)
    metres, position = index.tree.query(np.column_stack([x, y]))
    return Snap(node=index.nodes[position], metres=np.asarray(metres, dtype=np.float64))


def network_from(graph: nx.Graph, facilities: Snap) -> dict[object, float]:
    """Road distance from every node to its nearest facility, counting that facility's own snap.
    One Dijkstra from a virtual source joined to each facility's road node by its snap length."""
    joins: dict[object, float] = {}
    for node, metres in zip(facilities.node.tolist(), facilities.metres.tolist(), strict=True):
        joins[node] = min(metres, joins.get(node, math.inf))
    with_source = graph.copy()
    with_source.add_weighted_edges_from((SOURCE, node, metres) for node, metres in joins.items())
    lengths = nx.single_source_dijkstra_path_length(with_source, SOURCE, weight="weight")
    return {node: d for node, d in lengths.items() if node != SOURCE}


def cell_distances(lengths: dict[object, float], cells: Snap) -> np.ndarray:
    """Each cell's snap plus the network distance from its road node. Every node of a connected graph has one."""
    network = np.array([lengths.get(node, math.nan) for node in cells.node.tolist()])
    if np.isnan(network).any():
        raise RuntimeError("a cell's road node has no route to any facility; the graph should be one connected component")
    return cells.metres + network


def band_shares(distance: np.ndarray, people: np.ndarray, district: np.ndarray, districts: int) -> np.ndarray:
    """Percent of each district's residents under 1 km, 1 to 3 km and over 3 km. Shape (districts, 3)."""
    near, far = BAND_EDGES_M
    band = (distance >= near).astype(int) + (distance > far)  # 0: under 1 km, 1: 1 to 3 km inclusive, 2: over 3 km
    counts = np.zeros((districts, 3))
    np.add.at(counts, (district, band), people)
    return 100 * counts / counts.sum(axis=1, keepdims=True)


def largest_remainder(shares: Sequence[float], total: int = 100) -> tuple[int, ...]:
    """Round shares to whole numbers that sum to total, giving the leftover units to the largest fractional parts (earliest first on ties)."""
    floors = [math.floor(s) for s in shares]
    order = sorted(range(len(shares)), key=lambda i: (floors[i] - shares[i], i))
    extra = set(order[: total - sum(floors)])
    return tuple(f + (i in extra) for i, f in enumerate(floors))
```

- [ ] **Step 4: Run the tests**

Run (in `analysis/`): `uv run pytest tests/pulse/test_distance.py`, then `uv run pytest`.
Expected: `11 passed`, then `99 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/pulse/distance.py \
  analysis/tests/pulse/test_distance.py
git commit -m "feat: compute road distances and distance bands"
```

---

### Task 7: Python: the to-scale map geometry

**Files:**
- Create: `analysis/pulse/geometry.py`
- Test: `analysis/tests/pulse/test_geometry.py`

**Interfaces:**
- Consumes: `to_metres`, `LAT0` (`pulse.distance`, Task 6); `DISTRICTS`, `Bounds`, `Facility`, `load_districts` (`pulse.load`, Task 3); `read_osm` and the shapes of `Roads.bridges` and `Roads.places` (Task 5); `write_boundaries` (Task 3) and `write_osm`, `OSM_BBOX` (Task 5).
- Produces, in `pulse.geometry`: `VIEW_W = 600`, `VIEW_H = 500`, `MARGIN_PX`, `SIMPLIFY_PX`, `MIN_BRIDGE_M`, `WATER`, `LABEL_NUDGE_PX`; `Projection(x0, y0, scale, left, top)`; `fit(bounds) -> Projection`; `project(p, lon, lat) -> tuple[ndarray, ndarray]`; `project_geometry(p, geom)`; `path_d(geom) -> str`; `shared_edges(a, b) -> list[str]`; `bridge_path(p, lines, land) -> str`; `label(name, x, y) -> dict`; `map_geometry(districts, bridges, places) -> tuple[Projection, dict]`, the dict being the site's `PenangGeometry` (`island`, `mainland`, `districts` with `id`, `d`, `land`, `boundaries`, `bridges`, `places`, `water`); `points_json(p, facilities) -> list[dict]` with `category`, `x`, `y`.

One projection, fitted to all five districts with a 16 px margin, keeps the map to scale (on the real outlines: 9.1 px per km, the districts spanning x 110.9 to 489.1 and y 16 to 484). Outlines are simplified together with `shapely.coverage_simplify`, so shared edges stay shared; the real outlines need about 10 KB of path data. Bridges are drawn only where their ways cross water (on the real ways: four spans of 8.2 to 8.7 km for the Penang Bridge and four of 16.6 to 16.8 km for the second bridge, plus slivers under 300 m that are dropped). The George Town and Butterworth nodes sit about 40 px apart across the channel, so their centred labels overlapped in a render of the real data; `LABEL_NUDGE_PX` moves them 20 px apart, and Task 11 checks the result in a screenshot.

- [ ] **Step 1: Write the failing test**

Create `analysis/tests/pulse/test_geometry.py`:

```python
import re
from pathlib import Path

import numpy as np
import pytest

from pulse.distance import LAT0
from pulse.geometry import MARGIN_PX, VIEW_H, VIEW_W, fit, map_geometry, path_d, points_json, project
from pulse.load import Facility, load_districts
from pulse.roads import read_osm

from .world import OSM_BBOX, write_boundaries, write_osm

NUMBERS = re.compile(r"-?\d+\.?\d*")


def xy_of(d: str) -> np.ndarray:
    return np.array([float(v) for v in NUMBERS.findall(d)]).reshape(-1, 2)


@pytest.fixture
def drawn(tmp_path: Path) -> dict:
    roads = read_osm(write_osm(tmp_path), OSM_BBOX)
    return map_geometry(load_districts(write_boundaries(tmp_path)), roads.bridges, roads.places)[1]


def test_the_projection_keeps_the_aspect_ratio_and_fits_the_view_box() -> None:
    p = fit((100.20, 5.30, 100.30, 5.32))  # about 11 km wide and 2.2 km tall
    x, y = project(p, np.array([100.20, 100.30, 100.20]), np.array([5.30, 5.30, 5.32]))
    width, height = x[1] - x[0], y[0] - y[2]
    assert width == pytest.approx(VIEW_W - 2 * MARGIN_PX)
    assert width / height == pytest.approx(11_092 / 2_224, rel=0.01)  # metres east over metres north
    assert (y[0] + y[2]) / 2 == pytest.approx(VIEW_H / 2)  # centred vertically


def test_a_square_on_the_ground_stays_square_on_the_map() -> None:
    p = fit((100.20, 5.30, 100.30, 5.40))
    side = 0.01  # degrees of latitude; the same distance east needs side / cos(latitude) degrees of longitude
    x, y = project(p, np.array([100.25, 100.25 + side / np.cos(np.radians(LAT0))]), np.array([LAT0, LAT0 + side]))
    assert x[1] - x[0] == pytest.approx(y[0] - y[1])


def test_paths_draw_every_part_of_a_multipolygon(drawn: dict) -> None:
    timur_laut = drawn["districts"][0]["d"]
    assert timur_laut.count("M") == 2 and timur_laut.count("Z") == 2  # the district and its islet
    assert drawn["island"].count("M") == 2 and drawn["mainland"].count("M") == 1
    assert [d["land"] for d in drawn["districts"]] == ["island", "island", "mainland", "mainland", "mainland"]


def test_everything_sits_inside_the_view_box(drawn: dict) -> None:
    for d in [drawn["island"], drawn["mainland"], *drawn["boundaries"], *drawn["bridges"]]:
        xy = xy_of(d)
        assert (xy[:, 0] >= 0).all() and (xy[:, 0] <= VIEW_W).all() and (xy[:, 1] >= 0).all() and (xy[:, 1] <= VIEW_H).all()


def test_boundaries_are_the_three_shared_edges(drawn: dict) -> None:
    assert len(drawn["boundaries"]) == 3  # Timur Laut and Barat Daya; SP Utara and Tengah; SP Tengah and Selatan
    for d in drawn["boundaries"]:
        xy = xy_of(d)
        assert np.ptp(xy[:, 1]) == pytest.approx(0, abs=0.2)  # every shared edge in this world runs east to west


def test_bridges_are_drawn_only_over_water(drawn: dict) -> None:
    # Each bridge way starts and ends on land; only the stretch across the strait is drawn.
    p = fit((100.20, 5.30, 100.26, 5.36))
    (island_shore, main_shore), _ = project(p, np.array([100.22, 100.23]), np.array([5.33, 5.33]))
    for d in drawn["bridges"]:
        xy = xy_of(d)
        assert xy[:, 0].min() == pytest.approx(island_shore, abs=0.5)
        assert xy[:, 0].max() == pytest.approx(main_shore, abs=0.5)


def test_places_are_projected_town_labels(drawn: dict) -> None:
    assert [p["text"] for p in drawn["places"]] == ["George Town", "Bayan Lepas", "Balik Pulau", "Butterworth", "Bukit Mertajam", "Nibong Tebal"]
    george_town, butterworth = drawn["places"][0], drawn["places"][3]
    assert george_town["y"] == butterworth["y"] and george_town["x"] < butterworth["x"]


def test_facility_points_share_the_map_projection() -> None:
    p = fit((100.20, 5.30, 100.26, 5.36))
    points = points_json(p, [Facility("clinic", 100.20, 5.36, 2020), Facility("transit", 100.26, 5.30, None)])
    assert points[0]["category"] == "clinic" and points[1]["category"] == "transit"
    assert points[0]["x"] < points[1]["x"] and points[0]["y"] < points[1]["y"]
    assert (points[0]["x"], points[0]["y"]) == (round(p.left, 1), round(p.top, 1))
```

- [ ] **Step 2: Run the test to verify it fails**

Run (in `analysis/`): `uv run pytest tests/pulse/test_geometry.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse.geometry'`.

- [ ] **Step 3: Write the geometry**

Create `analysis/pulse/geometry.py`:

```python
"""Project districts, bridges, towns and facilities into the site's 600 by 500 map, to scale."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import shapely
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

from .distance import to_metres
from .load import DISTRICTS, Bounds, Facility

VIEW_W, VIEW_H = 600, 500
MARGIN_PX = 16
SIMPLIFY_PX = 0.8  # outlines lose detail finer than this, with shared edges simplified once
MIN_BRIDGE_M = 500.0  # pieces of a bridge's ways over water shorter than this are coastal slivers, not the span
WATER = {"text": "Selat Melaka", "x": 22, "y": 52}  # top left of the map is open sea west of the island
# ponytail: hand-set nudges, because the George Town and Butterworth nodes sit about 40 px apart across the channel and
# their centred labels would overlap. Replace with label collision handling if more labels are added.
LABEL_NUDGE_PX = {"George Town": (-20.0, 0.0), "Butterworth": (20.0, 0.0)}


@dataclass(frozen=True)
class Projection:
    x0: float  # metres east of Penang's centre at the left of the fitted box
    y0: float  # metres north at its bottom
    scale: float  # pixels per metre, the same both ways, so the map is to scale
    left: float  # pixels of padding that centre the fitted box
    top: float


def fit(bounds: Bounds) -> Projection:
    """The largest uniform scale that fits bounds inside the view box with a margin, centred."""
    (x0, x1), (y0, y1) = to_metres(np.array([bounds[0], bounds[2]]), np.array([bounds[1], bounds[3]]))
    scale = min((VIEW_W - 2 * MARGIN_PX) / (x1 - x0), (VIEW_H - 2 * MARGIN_PX) / (y1 - y0))
    return Projection(x0=float(x0), y0=float(y0), scale=float(scale), left=(VIEW_W - scale * (x1 - x0)) / 2, top=(VIEW_H - scale * (y1 - y0)) / 2)


def project(p: Projection, lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x, y = to_metres(lon, lat)
    return p.left + p.scale * (x - p.x0), VIEW_H - p.top - p.scale * (y - p.y0)


def project_geometry(p: Projection, geom: BaseGeometry) -> BaseGeometry:
    return shapely.transform(geom, lambda xy: np.column_stack(project(p, xy[:, 0], xy[:, 1])))


def path_d(geom: BaseGeometry) -> str:
    """SVG path data for polygons (closed rings) and lines, one decimal place."""
    def run(coords: np.ndarray) -> str:
        return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in coords)

    parts = []
    for part in shapely.get_parts(geom):
        if part.geom_type == "Polygon":
            parts.extend(run(np.asarray(ring.coords)[:-1]) + "Z" for ring in [part.exterior, *part.interiors])
        elif part.geom_type == "LineString":
            parts.append(run(np.asarray(part.coords)))
    return "".join(parts)


def shared_edges(a: BaseGeometry, b: BaseGeometry) -> list[str]:
    """The boundary two neighbouring districts share, merged into lines. Empty when they do not touch."""
    common = shapely.line_merge(shapely.union_all([g for g in shapely.get_parts(a.boundary.intersection(b.boundary)) if g.geom_type == "LineString"]))
    return [] if common.is_empty else [path_d(common)]


def bridge_path(p: Projection, lines: list[list[tuple[float, float]]], land: BaseGeometry) -> str:
    """Only the part of a bridge's ways that crosses water: its named approach roads and flyovers on land are left out."""
    over_water = project_geometry(p, shapely.union_all([LineString(line) for line in lines])).difference(land)
    spans = [g for g in shapely.get_parts(shapely.line_merge(over_water)) if g.length >= MIN_BRIDGE_M * p.scale]
    if not spans:
        raise ValueError("a bridge has no span over water; check the bridge names against OpenStreetMap")
    return "".join(path_d(g) for g in spans)


def label(name: str, x: float, y: float) -> dict[str, Any]:
    dx, dy = LABEL_NUDGE_PX.get(name, (0.0, 0.0))
    return {"text": name, "x": round(x + dx, 1), "y": round(y + dy, 1)}


def map_geometry(districts: Sequence[BaseGeometry], bridges: dict[str, list[list[tuple[float, float]]]], places: dict[str, tuple[float, float]]) -> tuple[Projection, dict[str, Any]]:
    """The PenangGeometry the site draws, and the projection used, so facilities can share it."""
    p = fit(shapely.union_all(list(districts)).bounds)
    outlines = shapely.coverage_simplify([project_geometry(p, d) for d in districts], SIMPLIFY_PX)
    lands = {land: [i for i, d in enumerate(DISTRICTS) if d.land == land] for land in ("island", "mainland")}
    pairs = [(i, j) for ids in lands.values() for k, i in enumerate(ids) for j in ids[k + 1 :]]
    land = shapely.union_all(list(outlines))
    labels = {name: project(p, np.array([lon]), np.array([lat])) for name, (lon, lat) in places.items()}
    return p, {
        "island": path_d(shapely.union_all([outlines[i] for i in lands["island"]])),
        "mainland": path_d(shapely.union_all([outlines[i] for i in lands["mainland"]])),
        "districts": [{"id": d.id, "d": path_d(outlines[i]), "land": d.land} for i, d in enumerate(DISTRICTS)],
        "boundaries": [edge for i, j in pairs for edge in shared_edges(outlines[i], outlines[j])],
        "bridges": [bridge_path(p, lines, land) for lines in bridges.values()],
        "places": [label(name, float(x[0]), float(y[0])) for name, (x, y) in labels.items()],
        "water": WATER,
    }


def points_json(p: Projection, facilities: Sequence[Facility]) -> list[dict[str, Any]]:
    x, y = project(p, np.array([f.lon for f in facilities]), np.array([f.lat for f in facilities]))
    return [{"category": f.category, "x": round(float(a), 1), "y": round(float(b), 1)} for f, a, b in zip(facilities, x, y, strict=True)]
```

- [ ] **Step 4: Run the tests**

Run (in `analysis/`): `uv run pytest tests/pulse/test_geometry.py`, then `uv run pytest`.
Expected: `8 passed`, then `107 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/pulse/geometry.py \
  analysis/tests/pulse/test_geometry.py
git commit -m "feat: project the Penang map to scale"
```

---

### Task 8: Python: prose templates and the results file

**Files:**
- Create: `analysis/pulse/export.py`
- Test: `analysis/tests/pulse/test_export.py`

**Interfaces:**
- Consumes: `largest_remainder` (`pulse.distance`, Task 6); `CATEGORIES`, `DISTRICTS` (`pulse.load`, Task 3).
- Produces, in `pulse.export`: `CLINIC, SCHOOL, TRANSIT` and `NEAR, MIDDLE, FAR` (axis indexes); `POINTS_NOTE`; `Findings(shares, transit_near, totals, counts, years)` where `shares` maps `"worldpop"` and `"meta"` to arrays of shape (districts, categories, bands) in percent; `pct(value: int) -> str`; `capital(text) -> str`; `join_names(names) -> str`; `long_date(iso) -> str`; `rounded(shares) -> ndarray`; `worst(shares) -> int`; `largest_far(r, category) -> str`; `answer_text(f) -> str`; `key_numbers(f, gtfs_retrieved: str) -> list[dict[str, str]]`; `district_entries(f) -> list[dict]`; `shares_json(shares) -> dict`; `build_results(f, geometry, points, run, retrieved, gtfs_retrieved) -> dict` in the site's `PenangResults` shape. Task 9 builds `Findings`; Task 12 parses the key number labels.

Rounding and ties, decided here because the spec leaves them open:
- Every whole percentage shown comes from one largest-remainder rounding per district and category, so a district's three bands sum to 100 and `far[category]` is that category's rounded over 3 km band. In particular `far.clinic` always equals `bands[2]`, which the web validator enforces; independent rounding could differ by one.
- `best` and `worst` use the unrounded clinic shares, the first district in the fixed order winning an exact tie, so each sentence names one district and states its own true figure. The school and transit sentence makes a superlative claim, so it names every district that shares the largest rounded share.
- The Meta sentence comes last, after the school and transit sentence (the spec calls it a third sentence, but it follows three).
- A share that rounds to 0 reads "under 1%", capitalised when it starts a sentence.

- [ ] **Step 1: Write the failing test**

Create `analysis/tests/pulse/test_export.py`:

```python
import re

import numpy as np
import pytest

from pulse.export import Findings, answer_text, district_entries, join_names, key_numbers, pct, shares_json

DASHES = re.compile("[–—]")
CLINIC = [(72.3, 23.5, 4.2), (48.2, 33.6, 18.2), (55.0, 33.0, 12.0), (61.0, 30.0, 9.0), (40.6, 38.2, 21.2)]
SCHOOL = [(90.0, 9.6, 0.4), (69.8, 25.0, 5.2), (81.0, 15.0, 4.0), (85.0, 12.0, 3.0), (59.6, 35.0, 5.4)]  # Barat Daya and SP Selatan tie at 5%
TRANSIT = [(95.0, 4.7, 0.3), (60.0, 20.0, 20.0), (70.0, 20.0, 10.0), (80.0, 15.0, 5.0), (50.0, 22.6, 27.4)]


def shares(clinic: list = CLINIC, school: list = SCHOOL, transit: list = TRANSIT) -> np.ndarray:
    return np.stack([np.array(clinic), np.array(school), np.array(transit)], axis=1)


def findings(worldpop: np.ndarray | None = None, meta: np.ndarray | None = None, transit_near: float = 57.6) -> Findings:
    wp = shares() if worldpop is None else worldpop
    return Findings(
        shares={"worldpop": wp, "meta": wp if meta is None else meta},
        transit_near=transit_near,
        totals=(556600, 237700, 339100, 423000, 184000),
        counts={"clinic": 120, "school": 432, "transit": 1885},
        years=(2013, 2022),
    )


def test_the_answer_names_the_best_and_worst_district_from_the_rounded_shares() -> None:
    assert answer_text(findings()) == (
        "In Timur Laut, 72% of residents live within 1 km of a public clinic by road. "
        "In Seberang Perai Selatan, 21% live more than 3 km away. "
        "For schools, the largest share more than 3 km away is 5%, in Barat Daya and Seberang Perai Selatan; "
        "for Rapid Penang stops, it is 27%, in Seberang Perai Selatan."
    )


def test_a_different_worst_district_with_meta_adds_a_sentence() -> None:
    meta_clinic = [*CLINIC[:1], (40.0, 35.0, 25.0), *CLINIC[2:]]
    assert answer_text(findings(meta=shares(clinic=meta_clinic))).endswith(
        "With Meta's 30 m population map instead of WorldPop, Barat Daya has the largest share more than 3 km from a clinic."
    )


def test_a_share_that_rounds_to_zero_reads_under_1_percent() -> None:
    low = [(99.5, 0.2, 0.3)] * 5
    text = answer_text(findings(shares(clinic=low, school=low, transit=low)))
    assert "In Timur Laut, under 1% live more than 3 km away." in text
    assert "is under 1%, in Timur Laut, Barat Daya, Seberang Perai Utara, Seberang Perai Tengah and Seberang Perai Selatan;" in text
    assert key_numbers(findings(transit_near=0.4), "2026-10-14")[2]["value"] == "under 1%"


def test_key_numbers_come_from_templates() -> None:
    meta_clinic = [*CLINIC[:4], (45.0, 36.0, 19.0)]
    assert key_numbers(findings(meta=shares(clinic=meta_clinic)), "2026-10-14T03:04:05+00:00") == [
        {
            "value": "21%",
            "label": "of Seberang Perai Selatan residents live more than 3 km by road from a public clinic.",
            "caveat": "19% with Meta's 30 m population map instead of WorldPop.",
        },
        {
            "value": "2,437",
            "label": "public clinics, schools and Rapid Penang stops mapped.",
            "caveat": "Dental clinics and private clinics are not included; facility records are dated 2013 to 2022.",
        },
        {
            "value": "58%",
            "label": "of Penang residents live within 1 km by road of a Rapid Penang stop.",
            "caveat": "Stops from the GTFS feed retrieved on 14 October 2026; distance says nothing about how often buses run.",
        },
    ]


def test_district_entries_keep_the_tiles_and_the_table_consistent() -> None:
    entries = district_entries(findings())
    assert [e["id"] for e in entries] == ["tl", "bd", "spu", "spt", "sps"]
    assert [e["short"] for e in entries] == ["Timur Laut", "Barat Daya", "SP Utara", "SP Tengah", "SP Selatan"]
    assert entries[0]["bands"] == [72, 24, 4] and entries[4]["bands"] == [41, 38, 21]
    assert all(sum(e["bands"]) == 100 and e["far"]["clinic"] == e["bands"][2] for e in entries)
    assert entries[4]["far"] == {"clinic": 21, "school": 5, "transit": 27}
    assert [e["population"] for e in entries] == [556600, 237700, 339100, 423000, 184000]


def test_helpers_and_copy_rules() -> None:
    assert [pct(0), pct(7)] == ["under 1%", "7%"]
    assert [join_names(["A"]), join_names(["A", "B"]), join_names(["A", "B", "C"])] == ["A", "A and B", "A, B and C"]
    assert shares_json(shares())["sps"]["transit"] == [50.0, 22.6, 27.4]
    prose = [answer_text(findings()), *(v for n in key_numbers(findings(), "2026-10-14") for v in n.values())]
    assert not any(DASHES.search(p) for p in prose)
```

- [ ] **Step 2: Run the test to verify it fails**

Run (in `analysis/`): `uv run pytest tests/pulse/test_export.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse.export'`.

- [ ] **Step 3: Write the exporter**

Create `analysis/pulse/export.py`:

```python
"""Turn the computed shares into the site's PenangResults JSON. All prose comes from templates over computed numbers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np

from .distance import largest_remainder
from .load import CATEGORIES, DISTRICTS

CLINIC, SCHOOL, TRANSIT = range(3)  # category axis, in CATEGORIES order
NEAR, MIDDLE, FAR = range(3)  # band axis: under 1 km, 1 to 3 km, over 3 km
POINTS_NOTE = "To scale. Every public clinic (dental excluded), school and Rapid Penang stop used. Dashed lines mark district boundaries."


@dataclass(frozen=True)
class Findings:
    shares: dict[str, np.ndarray]  # "worldpop" and "meta": percent of residents, shape (districts, categories, bands)
    transit_near: float  # percent of all Penang residents within 1 km of a stop, with WorldPop
    totals: tuple[int, ...]  # DOSM 2020 residents per district
    counts: dict[str, int]  # facilities used per category
    years: tuple[int, int]  # first and last record year of the clinics and schools


def pct(value: int) -> str:
    return "under 1%" if value == 0 else f"{value}%"


def capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def long_date(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{d.day} {d:%B %Y}"


def rounded(shares: np.ndarray) -> np.ndarray:
    """Whole percentages per district and category, each set of three bands summing to exactly 100."""
    return np.array([[largest_remainder(bands) for bands in district] for district in shares], dtype=int)


def worst(shares: np.ndarray) -> int:
    """The district with the largest unrounded share over 3 km from a clinic; the first in DISTRICTS order on a tie."""
    return int(np.argmax(shares[:, CLINIC, FAR]))


def largest_far(r: np.ndarray, category: int) -> str:
    """The largest rounded share over 3 km for a category, and every district that has it."""
    far = r[:, category, FAR]
    names = [DISTRICTS[i].name for i in np.flatnonzero(far == far.max())]
    return f"{pct(int(far.max()))}, in {join_names(names)}"


def answer_text(f: Findings) -> str:
    wp, meta = f.shares["worldpop"], f.shares["meta"]
    r = rounded(wp)
    best, bad = int(np.argmax(wp[:, CLINIC, NEAR])), worst(wp)
    sentences = [
        f"In {DISTRICTS[best].name}, {pct(int(r[best, CLINIC, NEAR]))} of residents live within 1 km of a public clinic by road.",
        f"In {DISTRICTS[bad].name}, {pct(int(r[bad, CLINIC, FAR]))} live more than 3 km away.",
        f"For schools, the largest share more than 3 km away is {largest_far(r, SCHOOL)}; for Rapid Penang stops, it is {largest_far(r, TRANSIT)}.",
    ]
    if worst(meta) != bad:
        sentences.append(f"With Meta's 30 m population map instead of WorldPop, {DISTRICTS[worst(meta)].name} has the largest share more than 3 km from a clinic.")
    return " ".join(sentences)


def key_numbers(f: Findings, gtfs_retrieved: str) -> list[dict[str, str]]:
    bad = worst(f.shares["worldpop"])
    q = int(rounded(f.shares["worldpop"])[bad, CLINIC, FAR])
    q_meta = int(rounded(f.shares["meta"])[bad, CLINIC, FAR])
    first, last = f.years
    return [
        {
            "value": pct(q),
            "label": f"of {DISTRICTS[bad].name} residents live more than 3 km by road from a public clinic.",
            "caveat": capital(f"{pct(q_meta)} with Meta's 30 m population map instead of WorldPop."),
        },
        {
            "value": f"{sum(f.counts.values()):,}",
            "label": "public clinics, schools and Rapid Penang stops mapped.",
            "caveat": f"Dental clinics and private clinics are not included; facility records are dated {first} to {last}.",
        },
        {
            "value": pct(round(f.transit_near)),
            "label": "of Penang residents live within 1 km by road of a Rapid Penang stop.",
            "caveat": f"Stops from the GTFS feed retrieved on {long_date(gtfs_retrieved)}; distance says nothing about how often buses run.",
        },
    ]


def district_entries(f: Findings) -> list[dict[str, Any]]:
    r = rounded(f.shares["worldpop"])
    return [
        {
            "id": d.id,
            "name": d.name,
            "short": d.short,
            "bands": [int(v) for v in r[i, CLINIC]],
            "population": f.totals[i],
            "far": {c: int(r[i, j, FAR]) for j, c in enumerate(CATEGORIES)},
        }
        for i, d in enumerate(DISTRICTS)
    ]


def shares_json(shares: np.ndarray) -> dict[str, dict[str, list[float]]]:
    """Unrounded shares to one decimal place, for the manifest."""
    return {d.id: {c: [round(float(v), 1) for v in shares[i, j]] for j, c in enumerate(CATEGORIES)} for i, d in enumerate(DISTRICTS)}


def build_results(f: Findings, geometry: dict[str, Any], points: list[dict[str, Any]], run: dict[str, str], retrieved: dict[str, str], gtfs_retrieved: str) -> dict[str, Any]:
    return {
        "answer": answer_text(f),
        "keyNumbers": key_numbers(f, gtfs_retrieved),
        "run": run,
        "retrieved": retrieved,
        "districts": district_entries(f),
        "points": points,
        "geometry": geometry,
        "pointsNote": POINTS_NOTE,
    }
```

- [ ] **Step 4: Run the tests**

Run (in `analysis/`): `uv run pytest tests/pulse/test_export.py`, then `uv run pytest`.
Expected: `6 passed`, then `113 passed`.

- [ ] **Step 5: Commit**

```bash
git add analysis/pulse/export.py \
  analysis/tests/pulse/test_export.py
git commit -m "feat: template the Penang Pulse results"
```

---

### Task 9: Python: the pipeline, the CLI and the manifest

**Files:**
- Create: `analysis/pulse/pipeline.py`, `analysis/pulse/cli.py`, `analysis/tests/pulse/conftest.py`, `analysis/tests/pulse/contract.py`
- Modify: `analysis/tests/pulse/world.py` (`write_inputs`)
- Test: `analysis/tests/pulse/test_pipeline.py`, `analysis/tests/pulse/test_cli.py`

**Interfaces:**
- Consumes: everything in Tasks 3 to 8; `git_state() -> {"commit", "dirty"}` (`forecasting.cli`) and `write_json(path, payload)` (`forecasting.export`), reused rather than copied.
- Produces, in `pulse.pipeline`: `ROAD_MARGIN_DEG = 0.05`, `POPULATION_MAPS = ("worldpop", "meta")`; `Inputs(health, schools, gtfs, dosm, boundaries, worldpop, meta, osm)` (rasters as GDAL path strings); `PulseRun(findings, geometry, points, outside, cells, roads)`; `read_facilities(inputs, land) -> list[Facility]`; `facility_network(graph, index, used, category)`; `map_shares(raster, districts, totals, index, lengths) -> tuple[ndarray, list[int], float]`; `run(inputs: Inputs) -> PulseRun`.
- Produces, in `pulse.cli`: `python -m pulse.cli [--raw-dir PATH]` (default `analysis/data/raw/pulse`), which writes `apps/web/src/content/results/penang-pulse.json` and `analysis/outputs/penang-pulse-manifest.json`; `build_manifest(fetched, result, packages, git) -> dict`; `RESULTS_PATH`, `MANIFEST_PATH`, `LIBRARIES`. Task 10 runs it.
- Produces, in tests: `check_results(results)` (`tests/pulse/contract.py`), the Python mirror of `parsePenangResults`; the session fixture `tiny_run` (`tests/pulse/conftest.py`); `write_inputs(folder) -> Inputs` (`tests/pulse/world.py`).

The CI job needs no change: it already runs `uv sync --locked` and `uv run pytest` in `analysis/`, and the new tests need no network.

- [ ] **Step 1: Write the failing tests**

In `analysis/tests/pulse/world.py`, replace the import block:

```python
from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import MultiPolygon, box, mapping

from pulse.sources import META_MEMBER
```

with:

```python
from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import MultiPolygon, box, mapping

from pulse.pipeline import Inputs
from pulse.population import meta_path
from pulse.sources import META_MEMBER
```

Append to `analysis/tests/pulse/world.py`:

```python
def write_inputs(folder: Path) -> Inputs:
    """Every input file of the synthetic world, as the pipeline takes them."""
    return Inputs(
        health=write_health(folder),
        schools=write_schools(folder),
        gtfs=write_gtfs(folder),
        dosm=write_dosm(folder),
        boundaries=write_boundaries(folder),
        worldpop=str(write_worldpop(folder)),
        meta=meta_path(write_meta(folder)),
        osm=write_osm(folder),
    )
```

Create `analysis/tests/pulse/contract.py`:

```python
"""The rules parsePenangResults (apps/web/src/content/results/parse-penang.ts) enforces, mirrored here so the
pipeline's own tests fail on a file the site would reject."""

from __future__ import annotations

import json
import math
import re
from typing import Any

DISTRICT_IDS = ["tl", "bd", "spu", "spt", "sps"]
CATEGORIES = ["clinic", "school", "transit"]
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def whole(value: Any, low: int, high: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def is_path(value: Any) -> bool:
    return text(value) and value.startswith("M")


def check_base(r: dict[str, Any]) -> None:
    assert text(r["answer"]), "answer"
    assert len(r["keyNumbers"]) == 3, "keyNumbers"
    assert all(text(k[f]) for k in r["keyNumbers"] for f in ("value", "label", "caveat")), "keyNumbers fields"
    assert all(text(r["run"][f]) for f in ("commit", "manifest", "python")) and ISO_DATE.match(r["run"]["lastRun"]), "run"
    assert r["retrieved"] and all(ISO_DATE.match(d) for d in r["retrieved"].values()), "retrieved"


def check_district(i: int, d: dict[str, Any]) -> None:
    assert d["id"] == DISTRICT_IDS[i] and text(d["name"]) and text(d["short"]), f"districts[{i}]"
    assert len(d["bands"]) == 3 and all(whole(b, 0, 100) for b in d["bands"]) and sum(d["bands"]) == 100, f"districts[{i}].bands"
    assert whole(d["population"], 1, 2**53 - 1), f"districts[{i}].population"
    assert all(whole(d["far"][c], 0, 100) for c in CATEGORIES) and d["far"]["clinic"] == d["bands"][2], f"districts[{i}].far"


def check_geometry(g: dict[str, Any]) -> None:
    assert is_path(g["island"]) and is_path(g["mainland"]), "geometry outlines"
    assert [d["id"] for d in g["districts"]] == DISTRICT_IDS and all(is_path(d["d"]) and d["land"] in ("island", "mainland") for d in g["districts"]), "geometry.districts"
    assert all(is_path(b) for b in g["boundaries"]), "geometry.boundaries"
    assert len(g["bridges"]) == 2 and all(is_path(b) for b in g["bridges"]), "geometry.bridges"
    assert len(g["places"]) == 6 and all(text(p["text"]) and number(p["x"]) and number(p["y"]) for p in [*g["places"], g["water"]]), "geometry labels"


def check_results(r: dict[str, Any]) -> None:
    json.dumps(r, allow_nan=False)  # NaN or infinity would not survive JSON
    check_base(r)
    assert len(r["districts"]) == 5, "districts"
    for i, d in enumerate(r["districts"]):
        check_district(i, d)
    assert r["points"] and all(p["category"] in CATEGORIES and number(p["x"]) and number(p["y"]) for p in r["points"]), "points"
    check_geometry(r["geometry"])
    assert text(r["pointsNote"]), "pointsNote"
```

Create `analysis/tests/pulse/conftest.py`:

```python
import pytest

from pulse.pipeline import PulseRun, run

from .world import write_inputs


@pytest.fixture(scope="session")
def tiny_run(tmp_path_factory: pytest.TempPathFactory) -> PulseRun:
    """One full pipeline run on the synthetic world, shared by the pipeline and CLI tests."""
    return run(write_inputs(tmp_path_factory.mktemp("world")))
```

Create `analysis/tests/pulse/test_pipeline.py`:

```python
from pathlib import Path

import pytest

from pulse.export import build_results
from pulse.pipeline import PulseRun

from .contract import check_results

RUN_INFO = {"commit": "abc1234", "manifest": "analysis/outputs/penang-pulse-manifest.json", "python": "3.12.9", "lastRun": "2026-10-14"}


def test_the_pipeline_writes_a_file_the_site_accepts(tiny_run: PulseRun) -> None:
    results = build_results(tiny_run.findings, tiny_run.geometry, tiny_run.points, RUN_INFO, {"OpenStreetMap": "2026-10-14"}, "2026-10-14T01:02:03+00:00")
    check_results(results)
    assert [d["population"] for d in results["districts"]] == [6000, 3000, 4000, 4500, 2500]
    assert results["keyNumbers"][1]["value"] == str(len(results["points"]))


def test_every_facility_used_is_a_point_and_the_dental_clinic_is_not(tiny_run: PulseRun) -> None:
    assert tiny_run.findings.counts == {"clinic": 3, "school": 3, "transit": 2}
    assert [p["category"] for p in tiny_run.points] == ["clinic"] * 3 + ["school"] * 3 + ["transit"] * 2
    assert tiny_run.outside == {"clinic": 1, "school": 0, "transit": 0}
    assert tiny_run.findings.years == (2013, 2022)


def test_both_population_maps_cover_every_district(tiny_run: PulseRun) -> None:
    assert tiny_run.cells == {"worldpop": [5, 6, 6, 6, 6], "meta": [5, 6, 6, 6, 6]}
    for shares in tiny_run.findings.shares.values():
        assert shares.shape == (5, 3, 3)
        assert shares.sum(axis=2) == pytest.approx(100)


def test_the_road_graph_drops_only_the_fragment(tiny_run: PulseRun) -> None:
    assert tiny_run.roads == {"nodes": 14, "edges": 14, "dropped_nodes": 2}


def test_the_map_has_both_bridges_and_all_six_towns(tiny_run: PulseRun) -> None:
    assert len(tiny_run.geometry["bridges"]) == 2
    assert len(tiny_run.geometry["places"]) == 6
    assert len(tiny_run.geometry["boundaries"]) == 3
```

Create `analysis/tests/pulse/test_cli.py`:

```python
import json
from pathlib import Path

from pulse.cli import build_manifest
from pulse.pipeline import PulseRun
from pulse.sources import Fetched


def fetched(tmp_path: Path, name: str, file: str) -> Fetched:
    path = tmp_path / file
    path.write_bytes(b"x")
    return Fetched(name, f"https://example.org/{file}", "CC BY", path, "2026-10-14T01:02:03+00:00", 1, "ab" * 32)


def test_manifest_records_the_provenance_of_a_run(tmp_path: Path, tiny_run: PulseRun) -> None:
    sources = [fetched(tmp_path, "Schools 2022", "schools.csv"), fetched(tmp_path, "OpenStreetMap", "malaysia-singapore-brunei-261013.osm.pbf")]
    manifest = build_manifest(sources, tiny_run, {"python": "3.12.9"}, {"commit": "abc1234", "dirty": False})

    assert manifest["sources"][0] == {
        "name": "Schools 2022",
        "url": "https://example.org/schools.csv",
        "licence": "CC BY",
        "retrieved": "2026-10-14T01:02:03+00:00",
        "bytes": 1,
        "sha256": "ab" * 32,
    }
    assert manifest["geofabrik_date"] == "2026-10-13"
    assert manifest["facilities"] == {"used": {"clinic": 3, "school": 3, "transit": 2}, "outside_districts": {"clinic": 1, "school": 0, "transit": 0}, "years": [2013, 2022]}
    assert manifest["roads"] == {"nodes": 14, "edges": 14, "dropped_nodes": 2}
    assert manifest["cells"]["meta"] == {"tl": 5, "bd": 6, "spu": 6, "spt": 6, "sps": 6}
    assert sorted(manifest["shares_percent"]) == ["meta", "worldpop"]
    assert len(manifest["shares_percent"]["worldpop"]["sps"]["school"]) == 3
    assert manifest["band_edges_m"] == [1000.0, 3000.0]
    assert manifest["git"] == {"commit": "abc1234", "dirty": False}
    assert manifest["results_file"] == "apps/web/src/content/results/penang-pulse.json"
    json.dumps(manifest, allow_nan=False)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (in `analysis/`): `uv run pytest tests/pulse`
Expected: FAIL. Importing `tests/pulse/conftest.py` stops with `ModuleNotFoundError: No module named 'pulse.pipeline'`, so no pulse test runs until the pipeline exists.

- [ ] **Step 3: Write the pipeline and the CLI**

Create `analysis/pulse/pipeline.py`:

```python
"""The whole study from input files to findings, map geometry and points. Pure: no downloads and no writing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import shapely
from shapely.geometry.base import BaseGeometry

from .distance import BAND_EDGES_M, RoadIndex, band_shares, cell_distances, network_from, road_index, snap
from .export import Findings
from .geometry import map_geometry, points_json
from .load import AREA_MARGIN_DEG, CATEGORIES, DISTRICTS, Facility, expand, load_districts, load_totals, outside_districts, read_clinics, read_schools, read_stops
from .population import read_cells
from .roads import read_osm

log = logging.getLogger(__name__)

ROAD_MARGIN_DEG = 0.05  # roads up to about 5 km outside the districts still carry routes between them
POPULATION_MAPS = ("worldpop", "meta")


@dataclass(frozen=True)
class Inputs:
    health: Path
    schools: Path
    gtfs: Path
    dosm: Path
    boundaries: Path
    worldpop: str  # a GDAL path
    meta: str  # a GDAL /vsizip/ path into the Meta zip
    osm: Path


@dataclass(frozen=True)
class PulseRun:
    findings: Findings
    geometry: dict[str, Any]
    points: list[dict[str, Any]]
    outside: dict[str, int]  # facilities kept although outside every district
    cells: dict[str, list[int]]  # populated cells per district, per population map
    roads: dict[str, int]  # graph nodes, edges, and nodes dropped outside the largest component


def read_facilities(inputs: Inputs, land: BaseGeometry) -> list[Facility]:
    area = expand(land.bounds, AREA_MARGIN_DEG)
    used = [*read_clinics(inputs.health, area), *read_schools(inputs.schools, area), *read_stops(inputs.gtfs, land)]
    for category in CATEGORIES:
        if not any(f.category == category for f in used):
            raise ValueError(f"no {category} facilities were read")
    return used


def facility_network(graph: nx.Graph, index: RoadIndex, used: list[Facility], category: str) -> dict[object, float]:
    chosen = [f for f in used if f.category == category]
    return network_from(graph, snap(index, np.array([f.lon for f in chosen]), np.array([f.lat for f in chosen])))


def map_shares(raster: str, districts: list[BaseGeometry], totals: list[int], index: RoadIndex, lengths: dict[str, dict[object, float]]) -> tuple[np.ndarray, list[int], float]:
    """Band shares per district, category and band for one population map, its cell counts, and the Penang-wide share within 1 km of a stop."""
    log.info("computing distances for %s", raster)
    cells = read_cells(raster, districts, totals)
    cell_snap = snap(index, cells.lon, cells.lat)
    distance = {c: cell_distances(lengths[c], cell_snap) for c in CATEGORIES}
    shares = np.stack([band_shares(distance[c], cells.people, cells.district, len(DISTRICTS)) for c in CATEGORIES], axis=1)
    transit_near = 100 * float(cells.people[distance["transit"] < BAND_EDGES_M[0]].sum() / cells.people.sum())
    return shares, np.bincount(cells.district, minlength=len(DISTRICTS)).tolist(), transit_near


def run(inputs: Inputs) -> PulseRun:
    districts = load_districts(inputs.boundaries)
    land = shapely.union_all(districts)
    totals = load_totals(inputs.dosm)
    used = read_facilities(inputs, land)
    counts = {c: sum(f.category == c for f in used) for c in CATEGORIES}
    outside = outside_districts(used, land)
    log.info("facilities used: %s; kept although outside every district: %s", counts, outside)

    roads = read_osm(inputs.osm, expand(land.bounds, ROAD_MARGIN_DEG))
    index = road_index(roads.graph)
    lengths = {c: facility_network(roads.graph, index, used, c) for c in CATEGORIES}

    per_map = {name: map_shares(raster, districts, totals, index, lengths) for name, raster in zip(POPULATION_MAPS, (inputs.worldpop, inputs.meta), strict=True)}

    years = [f.year for f in used if f.year is not None]
    findings = Findings(
        shares={name: shares for name, (shares, _, _) in per_map.items()},
        transit_near=per_map["worldpop"][2],
        totals=tuple(totals),
        counts=counts,
        years=(min(years), max(years)),
    )
    projection, geometry = map_geometry(districts, roads.bridges, roads.places)
    graph_size = {"nodes": roads.graph.number_of_nodes(), "edges": roads.graph.number_of_edges(), "dropped_nodes": roads.dropped}
    cells = {name: counts for name, (_, counts, _) in per_map.items()}
    return PulseRun(findings=findings, geometry=geometry, points=points_json(projection, used), outside=outside, cells=cells, roads=graph_size)
```

Create `analysis/pulse/cli.py`:

```python
"""Entry point: python -m pulse.cli (run from analysis/). Downloads every source, runs the study and writes its results."""

from __future__ import annotations

import argparse
import logging
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from forecasting.cli import git_state
from forecasting.export import write_json

from .distance import BAND_EDGES_M
from .export import build_results, shares_json
from .load import DISTRICTS
from .pipeline import Inputs, PulseRun, run
from .population import meta_path
from .sources import BOUNDARIES, DOSM, FILE_SOURCES, GTFS, HEALTH, META, OSM_NAME, SCHOOLS, WORLDPOP, Fetched, fetch, fetch_osm, geofabrik_date

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ANALYSIS_DIR.parent
RESULTS_PATH = REPO_DIR / "apps/web/src/content/results/penang-pulse.json"
MANIFEST_PATH = ANALYSIS_DIR / "outputs/penang-pulse-manifest.json"
LIBRARIES = ("numpy", "scipy", "networkx", "osmium", "pyarrow", "rasterio", "shapely")


def build_manifest(fetched: list[Fetched], result: PulseRun, packages: dict[str, str], git: dict[str, Any]) -> dict[str, Any]:
    osm = next(f for f in fetched if f.name == OSM_NAME)
    return {
        "study": "penang-pulse",
        "sources": [{"name": f.name, "url": f.url, "licence": f.licence, "retrieved": f.retrieved, "bytes": f.bytes, "sha256": f.sha256} for f in fetched],
        "geofabrik_date": geofabrik_date(osm.path.name),
        "facilities": {"used": result.findings.counts, "outside_districts": result.outside, "years": list(result.findings.years)},
        "roads": result.roads,
        "cells": {name: dict(zip([d.id for d in DISTRICTS], counts, strict=True)) for name, counts in result.cells.items()},
        "band_edges_m": list(BAND_EDGES_M),
        "shares_percent": {name: shares_json(shares) for name, shares in result.findings.shares.items()},
        "transit_within_1km_percent": round(result.findings.transit_near, 1),
        "packages": packages,
        "git": git,
        "results_file": str(RESULTS_PATH.relative_to(REPO_DIR)),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m pulse.cli", description="Run Penang Pulse and write its results.")
    parser.add_argument("--raw-dir", type=Path, default=ANALYSIS_DIR / "data/raw/pulse")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    files = {source: fetch(source, args.raw_dir) for source in FILE_SOURCES}
    osm = fetch_osm(args.raw_dir)
    inputs = Inputs(
        health=files[HEALTH].path,
        schools=files[SCHOOLS].path,
        gtfs=files[GTFS].path,
        dosm=files[DOSM].path,
        boundaries=files[BOUNDARIES].path,
        worldpop=str(files[WORLDPOP].path),
        meta=meta_path(files[META].path),
        osm=osm.path,
    )
    result = run(inputs)

    fetched = [*files.values(), osm]
    git = git_state()
    packages = {"python": platform.python_version(), **{name: version(name) for name in LIBRARIES}}
    write_json(MANIFEST_PATH, build_manifest(fetched, result, packages, git))
    run_info = {"commit": git["commit"], "manifest": str(MANIFEST_PATH.relative_to(REPO_DIR)), "python": packages["python"], "lastRun": datetime.now(UTC).date().isoformat()}
    retrieved = {f.name: f.retrieved[:10] for f in fetched}
    write_json(RESULTS_PATH, build_results(result.findings, result.geometry, result.points, run_info, retrieved, files[GTFS].retrieved))
    print(f"wrote {RESULTS_PATH.relative_to(REPO_DIR)} and {MANIFEST_PATH.relative_to(REPO_DIR)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and the help text**

Run (in `analysis/`): `uv run pytest tests/pulse`, `uv run pytest`, then `uv run python -m pulse.cli --help`, then `uv sync --locked`.
Expected: `63 passed`, then `119 passed`; a usage line `usage: python -m pulse.cli [-h] [--raw-dir RAW_DIR]`; and `uv sync --locked` exits 0 with nothing to change, as CI will run it.

- [ ] **Step 5: Commit**

```bash
git add analysis/pulse/pipeline.py \
  analysis/pulse/cli.py \
  analysis/tests/pulse/world.py \
  analysis/tests/pulse/contract.py \
  analysis/tests/pulse/conftest.py \
  analysis/tests/pulse/test_pipeline.py \
  analysis/tests/pulse/test_cli.py
git commit -m "feat: add the Penang Pulse pipeline, CLI and manifest"
```

---

### Task 10: The real run

**Files:**
- Create (written by the pipeline): `apps/web/src/content/results/penang-pulse.json`, `analysis/outputs/penang-pulse-manifest.json`
- Possibly modify: `analysis/pulse/roads.py` (`BRIDGES` or `PLACES` variants, only if Step 2 stops on a missing name)

**Interfaces:**
- Consumes: `python -m pulse.cli` (Task 9).
- Produces: the committed results file that Task 11 publishes and Task 12 quotes, and the manifest that its `run.manifest` names.

- [ ] **Step 1: Start from a clean tree**

Run: `git checkout -- apps/web/next-env.d.ts`, then `git status --porcelain`.
Expected: no output. The run records `git rev-parse --short HEAD` and whether the tree was dirty.

- [ ] **Step 2: Run the pipeline**

Run (in `analysis/`, in the background, with a timeout of at least 60 minutes): `uv run python -m pulse.cli 2>&1 | tee /tmp/pulse-run.log`
The first run downloads about 310 MB into `analysis/data/raw/pulse/` (the Geofabrik extract is about 250 MB and the Meta zip 42 MB). Reading the extract is the slow part: pyosmium fills node locations for all of Malaysia, Singapore and Brunei and Python looks only at road ways and place nodes. Distances and both population maps take seconds.
Expected log lines, in order: one `downloading ...` line per source on the first run; `read ... road ways and ... place nodes`; `road graph: ... nodes, ... edges; ... nodes outside the largest component dropped`; `facilities used: {'clinic': 120, 'school': 432, 'transit': 1885}; kept although outside every district: {'clinic': 2, 'school': 2, 'transit': 0}` (the transit count was 1,885 of 1,932 feed stops on 2026-10-14 and moves if the feed changes); two `computing distances for ...` lines; and last `wrote apps/web/src/content/results/penang-pulse.json and analysis/outputs/penang-pulse-manifest.json`.

If it stops:
- `... differs from ..., checked on 2026-10-14` for a fixed source: the publisher changed the file. Stop and tell Subashanan; do not edit the checksum.
- `OpenStreetMap has no road named ...` or `no place node named ...`: OSM renamed a feature. Look it up (for example `curl -s -A "observatory-analysis/0.1" "https://nominatim.openstreetmap.org/search?q=Penang+Bridge&format=jsonv2&namedetails=1"`), add the current `name` to that entry's variants in `BRIDGES` or to the matching check in `PLACES` in `analysis/pulse/roads.py`, run `uv run pytest`, and run again. Commit `roads.py` with this task.
- `a bridge has no span over water`: the bridge's ways no longer cross the district outlines' water; stop and report.

- [ ] **Step 3: Check the outputs**

Run (in `analysis/`):

```bash
uv run python - <<'EOF'
import json
m = json.load(open("outputs/penang-pulse-manifest.json"))
r = json.load(open("../apps/web/src/content/results/penang-pulse.json"))
for s in m["sources"]:
    print(s["name"], s["bytes"], s["sha256"][:8], s["retrieved"][:10])
print(m["geofabrik_date"], m["facilities"], m["roads"], m["git"])
print(m["cells"])
print([d["population"] for d in r["districts"]], len(r["points"]))
print(r["answer"])
for n in r["keyNumbers"]:
    print(n)
for d in r["districts"]:
    print(d["short"], d["bands"], d["far"])
EOF
uv run python -c "import json; from tests.pulse.contract import check_results; check_results(json.load(open('../apps/web/src/content/results/penang-pulse.json'))); print('valid')"
```

Expected:
- Sources with byte counts and checksum prefixes matching the spec: 26,373 `30d7abe1`; 145,133 `dc84127b`; GTFS 4,457,025 `9823a7c7` (or a logged drift); 264,746 `456bca23`; 1,932,621 `1a7db3b4`; 9,789,326 `b54a9a07`; 42,122,823 `31317c66`; then OpenStreetMap with the extract's size.
- A Geofabrik date from the last few days, facilities `{'used': {'clinic': 120, 'school': 432, 'transit': 1885}, 'outside_districts': {'clinic': 2, 'school': 2, 'transit': 0}, 'years': [2013, 2022]}`, a road graph of a few hundred thousand nodes with a small number dropped, and `'dirty': False`.
- Cells `{'worldpop': {'tl': 6811, 'bd': 6462, 'spu': 19339, 'spt': 16782, 'sps': 10677}, 'meta': {'tl': 42923, 'bd': 36306, 'spu': 65250, 'spt': 85402, 'sps': 47393}}` (checked on the real rasters during planning).
- Populations `[556600, 237700, 339100, 423000, 184000]` and 2,437 points (120 + 432 + 1,885).
- An answer and three key numbers in the Task 8 template shapes with no dashes, bands summing to 100, `far.clinic` equal to the third band, and `valid`.

Show Subashanan the answer, key numbers and the five districts' bands and `far` values now. The wording is approved at PR time; any change is made in `analysis/pulse/export.py` and the run repeated, never by editing the JSON.

- [ ] **Step 4: Check that the run reproduces**

The first run's two outputs are untracked files, which would make the rerun record `"dirty": true`, so move them aside first. Run (in `analysis/`):

```bash
mkdir -p /tmp/pp-run1 && mv ../apps/web/src/content/results/penang-pulse.json outputs/penang-pulse-manifest.json /tmp/pp-run1/
git status --porcelain
uv run python -m pulse.cli 2>&1 | tail -1
cmp /tmp/pp-run1/penang-pulse.json ../apps/web/src/content/results/penang-pulse.json && cmp /tmp/pp-run1/penang-pulse-manifest.json outputs/penang-pulse-manifest.json && echo identical
```

Expected: `git status --porcelain` prints nothing; the rerun (same day, every cached file reused, including the dated extract) prints the `wrote ...` line; then `identical`. If the files differ, find the source of nondeterminism before committing.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/content/results/penang-pulse.json analysis/outputs/penang-pulse-manifest.json
git commit -m "chore: publish the first Penang Pulse run"
```

If Step 2 changed `analysis/pulse/roads.py`, add it to this commit, and rerun before committing.

---

### Task 11: Web: publish the results and update the study record

**Files:**
- Modify: `apps/web/src/content/results/index.ts`, `apps/web/src/content/studies.ts`, `apps/web/src/content/fixtures/penang.ts`
- Test: `apps/web/src/content/results/index.test.ts` (replace), `apps/web/src/lib/study-results.test.ts`, `apps/web/src/components/study/study-page.test.tsx`, `apps/web/src/components/study/study-card.test.tsx` (modify)

**Interfaces:**
- Consumes: `parsePenangResults` (Task 2); `penang-pulse.json` (Task 10); `ServiceTable` inside `PenangFigure` (Task 1); `findStudy` (`content/studies.ts`).
- Produces: `published["penang-pulse"]`, a validated `PenangResults`; `getStudyResults("penang-pulse", env)` returns `{ data, preview: false }` in every environment. The study record lists eight sources whose names equal the keys of the results file's `retrieved`.

Once Penang Pulse is published, tests that used it as the unpublished or preview example switch to `llm-eval-lab`, which has a fixture and no published results.

- [ ] **Step 1: Write the failing tests**

Replace `apps/web/src/content/results/index.test.ts` with:

```ts
import { describe, expect, it } from "vitest";

import { findStudy } from "../studies";
import { published } from "./index";

const DASHES = /[–—]/; // en and em dashes

describe("published results", () => {
  const forecasting = published["forecasting-lab"]!;
  const pulse = published["penang-pulse"]!;

  it("publishes the forecasting lab from the validated results file", () => {
    expect(forecasting.models.map((m) => m.id)).toEqual(["persistence", "seasonal", "gb", "mlp", "chronos"]);
    expect(forecasting.horizons).toEqual([15, 30, 60, 90, 120]);
    expect(forecasting.sensors).toHaveLength(3);
  });

  it("publishes Penang Pulse from the validated results file", () => {
    expect(pulse.districts.map((d) => d.id)).toEqual(["tl", "bd", "spu", "spt", "sps"]);
    expect(pulse.geometry.bridges).toHaveLength(2);
    expect(Number(pulse.keyNumbers[1].value.replace(/,/g, ""))).toBe(pulse.points.length); // every facility counted is drawn
  });

  it.each(["forecasting-lab", "penang-pulse"] as const)("dates every source %s lists", (slug) => {
    for (const source of findStudy(slug)!.sources) {
      expect(published[slug]!.retrieved[source.name]).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it.each(["forecasting-lab", "penang-pulse"] as const)("%s points at its committed manifest and follows the copy rules", (slug) => {
    const data = published[slug]!;
    expect(data.run.manifest).toBe(`analysis/outputs/${slug}-manifest.json`);
    for (const line of [data.answer, ...data.keyNumbers.flatMap((n) => [n.label, n.caveat])]) {
      expect(line).not.toMatch(DASHES);
    }
  });
});
```

In `apps/web/src/lib/study-results.test.ts`, replace:

```ts
  it("returns nothing in production when no results are published", () => {
    expect(getStudyResults("penang-pulse", "production")).toBeNull();
    expect(getStudyResults("llm-eval-lab", "production")).toBeNull();
  });

  it("returns published results in every environment, never flagged as a preview", () => {
    for (const env of ["production", "development", "test", undefined]) {
      const loaded = getStudyResults("forecasting-lab", env);
      expect(loaded?.preview).toBe(false);
      expect(loaded?.data.models).toHaveLength(5);
    }
  });
```

with:

```ts
  it("returns nothing in production when no results are published", () => {
    expect(getStudyResults("llm-eval-lab", "production")).toBeNull();
    expect(getStudyResults("penang-ai-assistant", "production")).toBeNull();
  });

  it("returns published results in every environment, never flagged as a preview", () => {
    for (const env of ["production", "development", "test", undefined]) {
      const forecasting = getStudyResults("forecasting-lab", env);
      expect(forecasting?.preview).toBe(false);
      expect(forecasting?.data.models).toHaveLength(5);
      const pulse = getStudyResults("penang-pulse", env);
      expect(pulse?.preview).toBe(false);
      expect(pulse?.data.districts).toHaveLength(5);
    }
  });
```

Then, in the same file, replace `getStudyResults("penang-pulse", "staging")` with `getStudyResults("llm-eval-lab", "staging")` and `getStudyResults("penang-pulse")` with `getStudyResults("llm-eval-lab")`.

In `apps/web/src/components/study/study-page.test.tsx`, replace:

```tsx
const pulse = findStudy("penang-pulse")!;

describe("StudyPage", () => {
  it("production mode with no results shows the plan and no numbers", () => {
    const { container } = render(<StudyPage study={pulse} results={getStudyResults("penang-pulse", "production")} />);
    expect(screen.getByRole("heading", { level: 1, name: "Penang Pulse" })).toBeInTheDocument();
    expect(screen.getByText(pulse.plannedAnswer)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /the analysis is in progress/i })).toBeInTheDocument();
    expect(screen.queryAllByText("21%")).toHaveLength(0);
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
    expect(screen.queryByText("a1c9e04")).not.toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(0);
    expect(screen.getAllByText("Not yet retrieved")).toHaveLength(pulse.sources.length);
  });
```

with:

```tsx
const pulse = findStudy("penang-pulse")!;
const llm = findStudy("llm-eval-lab")!;

describe("StudyPage", () => {
  it("production mode with no results shows the plan and no numbers", () => {
    const { container } = render(<StudyPage study={llm} results={getStudyResults("llm-eval-lab", "production")} />);
    expect(screen.getByRole("heading", { level: 1, name: "LLM Eval Lab" })).toBeInTheDocument();
    expect(screen.getByText(llm.plannedAnswer)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /the analysis is in progress/i })).toBeInTheDocument();
    expect(screen.queryAllByText("3 points")).toHaveLength(0);
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
    expect(screen.queryByText("a1c9e04")).not.toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(0);
    expect(screen.getAllByText("Not yet retrieved")).toHaveLength(llm.sources.length);
  });

  it("production mode shows published Penang Pulse results, the service table and no preview label", () => {
    const loaded = getStudyResults("penang-pulse", "production")!;
    const { container } = render(<StudyPage study={pulse} results={loaded} />);
    expect(screen.getByText(loaded.data.answer)).toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(3);
    expect(screen.getByRole("table", { name: /more than 3 km by road from the nearest service/i })).toBeInTheDocument();
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
    expect(screen.queryAllByText("Not yet retrieved")).toHaveLength(0);
  });
```

Then, in the same file, replace:

```tsx
    render(<StudyPage study={pulse} results={getStudyResults("penang-pulse", "development")} />);
    expect(screen.getAllByText("21%").length).toBeGreaterThan(0);
```

with:

```tsx
    render(<StudyPage study={llm} results={getStudyResults("llm-eval-lab", "development")} />);
    expect(screen.getAllByText("3 points").length).toBeGreaterThan(0);
```

In `apps/web/src/components/study/study-card.test.tsx`, replace:

```tsx
    const { container } = render(<StudyCard study={pulse} results={getStudyResults("penang-pulse", "development")} headingLevel={3} />);
```

with:

```tsx
    const llm = findStudy("llm-eval-lab")!;
    const { container } = render(<StudyCard study={llm} results={getStudyResults("llm-eval-lab", "development")} headingLevel={3} />);
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/content/results/index.test.ts src/lib/study-results.test.ts src/components/study`
Expected: FAIL. `index.test.ts` fails with `Cannot read properties of undefined (reading 'districts')`; the `study-results` test fails with `expected undefined to be false`; the new study page test fails with `Cannot read properties of null (reading 'data')`. The tests moved to `llm-eval-lab` already pass.

- [ ] **Step 3: Publish the validated file**

Replace `apps/web/src/content/results/index.ts` with:

```ts
import type { StudyResultsBySlug } from "../types";
import forecastingLab from "./forecasting-lab.json";
import { parseForecastResults } from "./parse-forecast";
import { parsePenangResults } from "./parse-penang";
import penangPulse from "./penang-pulse.json";

// Real results written by the analysis pipelines in analysis/. Each file is validated on import,
// so a malformed file fails the build instead of reaching a page.
export const published: Partial<StudyResultsBySlug> = {
  "forecasting-lab": parseForecastResults(forecastingLab),
  "penang-pulse": parsePenangResults(penangPulse),
};
```

- [ ] **Step 4: Update the study record and the fixture's source names**

In `apps/web/src/content/studies.ts`, replace the whole object whose `slug` is `"penang-pulse"` (from its opening `{` to its closing `},`) with:

```ts
  {
    slug: "penang-pulse",
    title: "Penang Pulse",
    question: "How evenly are clinics, schools and transit stops spread across Penang?",
    status: "published",
    plannedAnswer:
      "This study will measure how far residents in each of Penang's districts live from the nearest public clinic, school and transit stop, and show where the gaps are widest.",
    figurePlan:
      "a map of public clinics, schools and transit stops, one tile per district showing the share of residents under 1 km, 1 to 3 km and over 3 km from the nearest clinic, and a table of the share over 3 km from each service.",
    data: "Penang open data, Rapid Penang GTFS, DOSM, WorldPop, OpenStreetMap.",
    tile: { motif: "diamond", a: "mustard", b: "jade", ground: "warm" },
    tint: "warm",
    themeClass: "s-pulse",
    sources: [
      { name: "Public health facilities 2022", publisher: "Penang State Government, via the data.gov.my archive", used: "Public clinics and hospitals, dental clinics excluded", licence: "CC BY" },
      { name: "Schools 2022", publisher: "Penang State Government, via the data.gov.my archive", used: "Every school, private schools included", licence: "CC BY" },
      { name: "Rapid Penang GTFS", publisher: "Prasarana, via data.gov.my", used: "Bus stops inside the five districts", licence: "CC BY 4.0" },
      { name: "Population by district", publisher: "DOSM, via OpenDOSM", used: "2020 population of each district", licence: "CC BY 4.0" },
      { name: "geoBoundaries MYS ADM2", publisher: "geoBoundaries, William & Mary geoLab", used: "District outlines", licence: "CC BY 3.0" },
      { name: "WorldPop 2020 constrained", publisher: "WorldPop, University of Southampton", used: "Where residents live, on a 100 m grid", licence: "CC BY 4.0" },
      { name: "Meta population map 2020", publisher: "Meta Data for Good, via HDX", used: "A 30 m population map, as a check", licence: "CC BY" },
      { name: "OpenStreetMap", publisher: "OpenStreetMap contributors, via Geofabrik", used: "Roads, bridges and town names", licence: "ODbL" },
    ],
    method: [
      "Take every public clinic and hospital except dental clinics, every school and every Rapid Penang stop inside the five districts.",
      "Spread each district's 2020 DOSM population over the populated cells of WorldPop's 100 m grid whose centre lies in the district.",
      "Build a road network from OpenStreetMap with footpaths, ferries and private roads left out, treating every road as two-way.",
      "For each populated cell, add the straight line to its nearest road, the road distance to the nearest facility and that facility's own straight line to the road.",
      "Band residents into under 1 km, 1 to 3 km and over 3 km for each service, and repeat with Meta's 30 m population map as a check.",
    ],
    limitations: [
      "Facility records are dated 2013 to 2022 and come from a legacy open data portal.",
      "Private clinics are not included, and 32 private schools are.",
      "Population is modelled on a 100 m grid, not counted.",
      "Road distance is not travel time, and says nothing about how often buses run.",
      "Every road is treated as two-way.",
    ],
    reproduce: {
      commands: ["cd analysis", "uv sync", "uv run python -m pulse.cli", "cd .. && npm run dev"],
      note: "The first run downloads about 310 MB of source data into analysis/data/raw/pulse. The tests need none of it: uv run pytest.",
    },
    discussNote: "Spotted a missing clinic or a better boundary file? Questions and corrections are welcome.",
  },
```

The planned answer is unchanged and has no numbers. The limitations' dates and the count of private schools are facts about the sources, stated by the spec, not results. Source names must match `pulse/sources.py` exactly, because the sources table looks up each name in `retrieved`.

`content.test.ts` checks that every fixture dates every source its study lists. In `apps/web/src/content/fixtures/penang.ts`, replace:

```ts
  retrieved: { PeGIS: "2026-09-28", "Census 2020": "2026-09-28", OpenStreetMap: "2026-09-29" },
```

with:

```ts
  retrieved: {
    "Public health facilities 2022": "2026-09-28",
    "Schools 2022": "2026-09-28",
    "Rapid Penang GTFS": "2026-09-28",
    "Population by district": "2026-09-28",
    "geoBoundaries MYS ADM2": "2026-09-28",
    "WorldPop 2020 constrained": "2026-09-28",
    "Meta population map 2020": "2026-09-28",
    OpenStreetMap: "2026-09-29",
  },
```

- [ ] **Step 5: Run every check, and prove a bad file fails the build**

Run: `npm test`, `npm run lint`, `npm run typecheck`, then `npm run build`.
Expected: `Tests  145 passed (145)`, no lint or type errors, and the build lists `/work/penang-pulse` under `●  (SSG)`.

Then break the file on purpose and build again:

```bash
cp apps/web/src/content/results/penang-pulse.json /tmp/penang-pulse.json
node -e "const f='apps/web/src/content/results/penang-pulse.json';const fs=require('fs');const d=JSON.parse(fs.readFileSync(f));fs.writeFileSync(f,JSON.stringify({...d,geometry:{...d.geometry,bridges:d.geometry.bridges.slice(1)}}))"
npm run build 2>&1 | grep "penang-pulse results"
cp /tmp/penang-pulse.json apps/web/src/content/results/penang-pulse.json
git diff --stat apps/web/src/content/results/penang-pulse.json
```

Expected: the build fails and the grep prints a line ending `Error: penang-pulse results: geometry.bridges must have 2 items, found 1`; after the copy back, `git diff --stat` prints nothing.

- [ ] **Step 6: Restore the generated file**

Run: `git checkout -- apps/web/next-env.d.ts`

- [ ] **Step 7: Check the page against the JSON**

From `apps/web`, run `npx next start --port 3001` in the background, then `curl -s http://localhost:3001/work/penang-pulse | grep -o "Preview with illustrative data" | head -1`.
Expected: no output. Open `http://localhost:3001/work/penang-pulse` and check that the answer, the three key numbers, each district tile, the table and the "Retrieved" dates match `penang-pulse.json` exactly, and that the status pill reads "Published".

- [ ] **Step 8: Screenshot the figure**

With the server still running, from the repository root:

```bash
npx -y playwright@1.59 screenshot --full-page --wait-for-timeout=1500 --viewport-size=1440,900 http://localhost:3001/work/penang-pulse .context/pp-real-1440.png
npx -y playwright@1.59 screenshot --full-page --wait-for-timeout=1500 --viewport-size=390,844 http://localhost:3001/work/penang-pulse .context/pp-real-390.png
```

Look at both. Expected: island and mainland outlines to scale, with dashed boundaries inside each land mass; both bridges drawn only across the water; six town labels, George Town on the island and Butterworth on the mainland without overlapping; the table in dark text on white with the selected district's row shaded, and all four columns visible at 390 px without sideways scrolling. If two labels still collide, adjust `LABEL_NUDGE_PX` in `analysis/pulse/geometry.py`, rerun Task 10 Step 2, and commit both files with this task. Stop the server.

- [ ] **Step 9: Commit**

```bash
git add apps/web/src/content/results/index.ts apps/web/src/content/results/index.test.ts apps/web/src/content/studies.ts \
  apps/web/src/content/fixtures/penang.ts apps/web/src/lib/study-results.test.ts \
  apps/web/src/components/study/study-page.test.tsx apps/web/src/components/study/study-card.test.tsx
git commit -m "feat: publish real Penang Pulse results"
```

---

### Task 12: The CV bullet, final checks and the pull request

**Files:**
- Replace: `analysis/tools/update_cv.py`
- Modify: `apps/web/public/subashanan-nair-cv.pdf`
- Modify, not committed: `.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf`, with before and after renders in `.context/resume/`
- Test: `analysis/tests/test_update_cv.py`

**Interfaces:**
- Consumes: `apps/web/src/content/results/penang-pulse.json` (Task 10): `keyNumbers[0]` (value and the label `of <district> residents live more than 3 km by road from a public clinic.`), `keyNumbers[1].value` and `keyNumbers[2].value`; `forecasting-lab.json` as before.
- Produces: `python tools/update_cv.py SOURCE TARGET --png-dir DIR`, safe to run again on its own output; helpers `pulse_text(results) -> tuple[str, ...]`, `text_lines(page) -> list[TextLine]`, `bullet_lines(page, starts: tuple[str, ...]) -> list[Line]`, `replace_tech_line(page, old: tuple[str, ...], new, fitz)`; constants `PULSE_BULLET`, `PULSE_TECH_OLD`, `PULSE_TECH_NEW`, `FORECAST_BULLET`, `LINE_GAP`. `PULSE_TEXT` (the "In progress" wording) is removed.

Why the tool changes shape: on today's PDFs the earlier run left the bullet glyph as its own line and inserted the text as separate Helvetica lines, and both tech lines no longer read their old text, so the current `main` would stop. Each edit now finds its entry in any known state (the original wording, the earlier run's wording, or this run's), so the same command works on both PDFs and on its own output. The Penang Pulse tech line still names Pydantic and Penang GeoHub, which the new pipeline does not use; it is swapped for the libraries and data the pipeline does use, as was done for the Forecasting Lab line (spec section 17 of the Forecasting Lab spec). This goes beyond spec section 11; Subashanan approved it on 2026-10-14. A dry run during planning, with placeholder key numbers, fitted the first wording in the bullet's three lines on both PDFs and on the original attachment, and a second run on the output changed nothing.

- [ ] **Step 1: Write the failing tests**

In `analysis/tests/test_update_cv.py`, replace:

```python
from tools.update_cv import FORECAST_TECH_NEW, FORECAST_TECH_OLD, change, choose, forecast_text, wrap
```

with:

```python
from tools.update_cv import FORECAST_TECH_NEW, FORECAST_TECH_OLD, PULSE_BULLET, PULSE_TECH_NEW, bullet_lines, change, choose, forecast_text, pulse_text, wrap
```

Append to `analysis/tests/test_update_cv.py`:

```python
PULSE = {
    "keyNumbers": [
        {"value": "21%", "label": "of Seberang Perai Selatan residents live more than 3 km by road from a public clinic."},
        {"value": "2,437", "label": "public clinics, schools and Rapid Penang stops mapped."},
        {"value": "58%", "label": "of Penang residents live within 1 km by road of a Rapid Penang stop."},
    ]
}


def test_pulse_text_uses_only_numbers_from_the_results() -> None:
    preferred, spec, short = pulse_text(PULSE)
    assert preferred == (
        "Road distance from every populated 100 m cell in Penang to the nearest of 2,437 public clinics, schools and bus stops. "
        "21% of Seberang Perai Selatan residents live over 3 km from a clinic; 58% of all residents live within 1 km of a bus stop."
    )
    assert spec == (
        "Road distance from every populated 100 m cell in Penang to the nearest public clinic, school and bus stop; "
        "21% of Seberang Perai Selatan residents live over 3 km from a clinic."
    )
    assert short.startswith("Road distance from every populated cell")
    assert all(text.startswith(PULSE_BULLET[-1]) for text in (preferred, spec, short))  # so a later run finds the bullet again


def test_pulse_text_capitalises_a_share_under_1_percent_that_starts_a_sentence() -> None:
    low = {"keyNumbers": [{**PULSE["keyNumbers"][0], "value": "under 1%"}, *PULSE["keyNumbers"][1:]]}
    assert " stops. Under 1% of Seberang Perai Selatan" in pulse_text(low)[0]
    assert "; under 1% of Seberang Perai Selatan" in pulse_text(low)[1]


def test_pulse_tech_line_names_what_the_pipeline_uses() -> None:
    assert "Pydantic" not in PULSE_TECH_NEW and "Penang GeoHub" not in PULSE_TECH_NEW
    assert all(name in PULSE_TECH_NEW for name in ("NetworkX", "rasterio", "Shapely", "pyosmium", "OpenStreetMap", "WorldPop", "DOSM data"))


def raw_line(x: float, baseline: float, text: str, font: str = "Helvetica", size: float = 9.5) -> dict:
    chars = [{"c": c, "bbox": (x + 5 * i, baseline - 9, x + 5 * i + 5, baseline + 3)} for i, c in enumerate(text)]
    return {"bbox": (x, baseline - 10, x + 5 * len(text), baseline + 3), "spans": [{"size": size, "font": font, "origin": (x, baseline), "chars": chars}]}


class FakePage:
    def __init__(self, *lines: dict) -> None:
        self.lines = lines

    def get_text(self, kind: str) -> dict:
        return {"blocks": [{"lines": [line]} for line in reversed(self.lines)]}  # out of order, as inserted text is


def test_bullet_lines_finds_text_an_earlier_run_inserted_beside_its_bullet() -> None:
    page = FakePage(
        raw_line(54.8, 169.7, "•  ", font="LiberationSans"),
        raw_line(63.4, 169.7, "In progress: a reproducible study of how far"),
        raw_line(64.9, 181.1, "and transit stop, using PeGIS"),
        raw_line(64.9, 192.5, "limitations are published ahead of any results."),
        raw_line(50.5, 207.3, "Forecasting Lab", font="LiberationSans-Bold", size=10.0),
    )
    assert [(line.x, line.baseline) for line in bullet_lines(page, PULSE_BULLET)] == [(63.4, 169.7), (64.9, 181.1), (64.9, 192.5)]


def test_bullet_lines_finds_the_original_bullet_and_stops_at_the_next_one() -> None:
    page = FakePage(
        raw_line(54.8, 169.7, "•  Reproducible study of how evenly clinics", font="LiberationSans"),
        raw_line(64.9, 181.1, "schools and transit stops", font="LiberationSans"),
        raw_line(54.8, 192.5, "•  Another bullet", font="LiberationSans"),
    )
    assert [(line.x, line.baseline) for line in bullet_lines(page, PULSE_BULLET)] == [(54.8 + 15, 169.7), (64.9, 181.1)]
    with pytest.raises(SystemExit, match="No line starts with"):
        bullet_lines(page, ("Leakage safe",))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (in `analysis/`): `uv run pytest tests/test_update_cv.py`
Expected: FAIL with `ImportError: cannot import name 'pulse_text' from 'tools.update_cv'`.

- [ ] **Step 3: Replace the tool**

Replace `analysis/tools/update_cv.py` with:

```python
"""Rewrites the Forecasting Lab and Penang Pulse entries on page 2 of the CV from the published results.

Each edit finds the entry in any of its known states (the original wording or an earlier run of this tool), so running it
again on an updated CV is safe.

Run from analysis/:
  uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py SOURCE.pdf TARGET.pdf --png-dir DIR
SOURCE and TARGET may be the same file. PyMuPDF is imported inside main(), so the tests need only the standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_DIR = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_DIR / "apps/web/src/content/results"
PAGE = 1  # zero-based: the projects page
RIGHT_EDGE = 562.0  # widest existing body line ends at 561.8
BODY = {"fontname": "helv", "fontsize": 9.5, "color": (0, 0, 0)}  # LiberationSans is metric-compatible with Helvetica
TECH = {"fontname": "heit", "fontsize": 8.5, "color": (0x55 / 255,) * 3}  # Helvetica-Oblique for the grey tech lines
LINE_GAP = 15.0  # baselines further apart than this belong to different entries
FORECAST_BULLET = ("Leakage safe 15 minute traffic forecasting",)
PULSE_BULLET = ("Reproducible study of how evenly clinics", "In progress: a reproducible study", "Road distance from every")
FORECAST_TECH_OLD = "Python, scikit-learn, NumPy, SciPy, Pydantic, UCI dataset 608"
FORECAST_TECH_NEW = "Python, scikit-learn, NumPy, SciPy, PyTorch, Chronos, UCI dataset 608"
PULSE_TECH_OLD = (
    "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js, React Three Fiber",
    "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js",
)
PULSE_TECH_NEW = "Python, NumPy, SciPy, NetworkX, rasterio, Shapely, pyosmium, OpenStreetMap, WorldPop, DOSM data, Next.js"

Width = Callable[[str], float]


@dataclass(frozen=True)
class Line:
    x: float  # where the text starts, after any bullet
    baseline: float
    top: float
    bottom: float


@dataclass(frozen=True)
class TextLine:
    line: Line
    text: str  # without a leading bullet
    size: float
    bold: bool
    bullet: bool  # starts with a bullet glyph


def change(name: str, percent: float) -> str:
    return f"{'fell' if percent >= 0 else 'rose'} {round(abs(percent))}% with {name}"


HEADLINE_LABEL = re.compile(r"^lower error than persistence for (?P<name>.+) at \d+ minutes\.$")
HEADLINE_INTERVAL = re.compile(r"95% interval (?P<low>\d+) to (?P<high>\d+)%")
CHRONOS_LABEL = re.compile(r"^lower error for Chronos, with no tuning, than (?P<name>.+) at \d+ hours\.$")


def headline_text(results: dict[str, Any], head: str) -> str | None:
    """The wording with the published interval, parsed from keyNumbers. None unless both changes are reductions."""
    short, long = results["keyNumbers"][0], results["keyNumbers"][1]
    label, chronos_label = HEADLINE_LABEL.match(short["label"]), CHRONOS_LABEL.match(long["label"])
    interval = HEADLINE_INTERVAL.search(short["caveat"])
    if not (label and chronos_label and interval):
        return None
    hours = results["horizons"][-1] // 60
    name, rival = label["name"], chronos_label["name"]
    return (
        f"{head} {name[0].upper()}{name[1:]} cut MAE {short['value']} (95% interval {interval['low']} to {interval['high']}%) "
        f"versus persistence at {results['horizons'][0]} minutes; zero-shot Chronos beat {'it' if rival == name else rival} "
        f"by {long['value']} at {hours} hours."
    )


def forecast_text(results: dict[str, Any]) -> tuple[str, ...]:
    """Candidate wordings, preferred first, built only from numbers in the results file."""
    first = {m["id"]: m["mae"][0] for m in results["models"]}
    cut = {k: 100 * (1 - first[k] / first["persistence"]) for k in ("gb", "mlp", "chronos")}
    minutes = results["horizons"][0]
    sensors = results["keyNumbers"][2]["value"]
    head = f"Leakage safe {minutes} minute traffic forecasting benchmark across a {sensors} sensor network."
    full = (
        f"{head} At {minutes} minutes versus persistence, MAE {change('gradient boosting', cut['gb'])}, "
        f"{change('a spatial MLP', cut['mlp'])} and {change('zero-shot Chronos', cut['chronos'])}."
    )
    short = f"{head} At {minutes} minutes, MAE {change('gradient boosting', cut['gb'])} versus persistence."
    preferred = headline_text(results, head)
    return (full, short) if preferred is None else (preferred, full, short)


PULSE_LABEL = re.compile(r"^of (?P<district>.+) residents live more than 3 km by road from a public clinic\.$")


def pulse_text(results: dict[str, Any]) -> tuple[str, ...]:
    """Candidate wordings, preferred first, built only from the key numbers in the results file. All start with PULSE_BULLET[-1]."""
    far, count, transit = results["keyNumbers"]
    label = PULSE_LABEL.match(far["label"])
    if label is None:
        raise SystemExit(f"Unexpected Penang Pulse key number label: {far['label']!r}")
    claim = f"{far['value']} of {label['district']} residents live over 3 km from a clinic"
    return (
        f"Road distance from every populated 100 m cell in Penang to the nearest of {count['value']} public clinics, schools and bus stops. "
        f"{claim[0].upper()}{claim[1:]}; {transit['value']} of all residents live within 1 km of a bus stop.",
        f"Road distance from every populated 100 m cell in Penang to the nearest public clinic, school and bus stop; {claim}.",
        f"Road distance from every populated cell in Penang to the nearest clinic, school and bus stop; {claim}.",
    )


def wrap(text: str, width: Width, limits: list[float]) -> list[str] | None:
    """Greedy word wrap into at most len(limits) lines, line i no wider than limits[i]. None when it does not fit."""
    lines: list[str] = []
    for word in text.split():
        if lines and width(f"{lines[-1]} {word}") <= limits[len(lines) - 1]:
            lines[-1] = f"{lines[-1]} {word}"
        elif len(lines) < len(limits) and width(word) <= limits[len(lines)]:
            lines.append(word)
        else:
            return None
    return lines


def choose(candidates: tuple[str, ...], width: Width, limits: list[float]) -> list[str]:
    for text in candidates:
        lines = wrap(text, width, limits)
        if lines is not None:
            return lines
    raise SystemExit(f"No wording fits in {len(limits)} lines; shorten the candidates: {candidates[-1]!r}")


def text_lines(page: Any) -> list[TextLine]:
    """Every text line on the page in reading order, with any leading bullet glyph removed. A bullet on its own is skipped."""
    found = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            chars = [c for span in line["spans"] for c in span["chars"]]
            lead = next((i for i, c in enumerate(chars) if c["c"] not in "• "), len(chars))
            if lead == len(chars):
                continue
            span = line["spans"][0]
            at = Line(x=chars[lead]["bbox"][0], baseline=span["origin"][1], top=line["bbox"][1], bottom=line["bbox"][3])
            text = "".join(c["c"] for c in chars[lead:])
            found.append(TextLine(at, text, round(span["size"], 1), "Bold" in span["font"], chars[0]["c"] == "•"))
    return sorted(found, key=lambda t: (t.line.baseline, t.line.x))


def bullet_lines(page: Any, starts: tuple[str, ...]) -> list[Line]:
    """The line starting with one of `starts`, then its continuation lines: same size, no bullet, not bold, close below."""
    lines = text_lines(page)
    first = next((i for i, t in enumerate(lines) if t.text.startswith(starts)), None)
    if first is None:
        raise SystemExit(f"No line starts with any of {starts}")
    found = [lines[first]]
    for t in lines[first + 1 :]:
        if t.size != found[0].size or t.bold or t.bullet or t.line.baseline - found[-1].line.baseline > LINE_GAP:
            break
        found.append(t)
    return [t.line for t in found]


def replace_bullet(page: Any, starts: tuple[str, ...], candidates: tuple[str, ...], fitz: Any) -> None:
    targets = bullet_lines(page, starts)
    width = lambda s: fitz.get_text_length(s, fontname=BODY["fontname"], fontsize=BODY["fontsize"])  # noqa: E731
    text = choose(candidates, width, [RIGHT_EDGE - line.x for line in targets])
    for line in targets:
        page.add_redact_annot(fitz.Rect(line.x + 0.2, line.top + 0.5, RIGHT_EDGE + 1, line.bottom - 0.5), fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for line, words in zip(targets, text, strict=False):
        page.insert_text((line.x, line.baseline), words, **BODY)


def replace_tech_line(page: Any, old: tuple[str, ...], new: str, fitz: Any) -> None:
    """Swap the grey tech line that reads any of `old`, or `new` from an earlier run, for `new`."""
    spans = [s for b in page.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"] if s["text"] in (*old, new)]
    if len(spans) != 1:
        raise SystemExit(f"Expected one tech line reading one of {(*old, new)}, found {len(spans)}")
    span = spans[0]
    end = span["origin"][0] + fitz.get_text_length(new, fontname=TECH["fontname"], fontsize=TECH["fontsize"])
    if end > RIGHT_EDGE:
        raise SystemExit(f"Tech line {new!r} ends at x = {end:.1f}, past {RIGHT_EDGE}")
    page.add_redact_annot(fitz.Rect(span["bbox"]), fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    page.insert_text(span["origin"], new, **TECH)


def render(doc: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc[PAGE].get_pixmap(dpi=110).save(path)


def main(argv: list[str] | None = None) -> None:
    import fitz  # PyMuPDF

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--png-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    forecast = json.loads((RESULTS_DIR / "forecasting-lab.json").read_text())
    pulse = json.loads((RESULTS_DIR / "penang-pulse.json").read_text())
    doc = fitz.open(args.source)
    render(doc, args.png_dir / f"{args.target.stem}-before.png")
    page = doc[PAGE]
    replace_tech_line(page, PULSE_TECH_OLD, PULSE_TECH_NEW, fitz)
    replace_tech_line(page, (FORECAST_TECH_OLD,), FORECAST_TECH_NEW, fitz)
    replace_bullet(page, PULSE_BULLET, pulse_text(pulse), fitz)
    replace_bullet(page, FORECAST_BULLET, forecast_text(forecast), fitz)
    render(doc, args.png_dir / f"{args.target.stem}-after.png")
    args.target.parent.mkdir(parents=True, exist_ok=True)
    scratch = args.target.with_suffix(".tmp.pdf")
    doc.save(scratch, garbage=3, deflate=True)
    doc.close()
    os.replace(scratch, args.target)
    print(f"wrote {args.target}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests**

Run (in `analysis/`): `uv run pytest tests/test_update_cv.py`, then `uv run pytest`.
Expected: `12 passed`, then `124 passed`.

- [ ] **Step 5: Inspect the spans before editing**

Run (in `analysis/`):

```bash
uv run --no-project --with pymupdf==1.26.7 python -c "
import fitz, sys
for path in sys.argv[1:]:
    page = fitz.open(path)[1]
    print('==', path)
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                if 130 < s['bbox'][1] < 250:
                    print([round(v, 1) for v in s['bbox']], s['font'], round(s['size'], 1), repr(s['text']))
" "../.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf" ../apps/web/public/subashanan-nair-cv.pdf
```

Expected, for both files: the Penang Pulse tech line in `Helvetica-Oblique` 8.5 reading `Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js`; a `'•  '` span in `LiberationSans` 9.5 at x 54.8; three `Helvetica` 9.5 lines starting `'In progress: a reproducible study'` at x 63.4, then 64.9 and 64.9; and the two Forecasting Lab lines starting `'Leakage safe 15 minute traffic forecasting'`. If the layout differs, stop and report it instead of running Step 6.

- [ ] **Step 6: Update both PDFs**

Run (in `analysis/`):

```bash
uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py \
  "../.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf" \
  "../.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf" --png-dir ../.context/resume
uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py \
  ../apps/web/public/subashanan-nair-cv.pdf ../apps/web/public/subashanan-nair-cv.pdf --png-dir ../.context/resume
```

Expected: two `wrote ...` lines. If either prints `No wording fits`, shorten the candidates in `pulse_text` (the words, never the numbers), keep every candidate starting with `Road distance from every`, rerun the tests, and repeat.

- [ ] **Step 7: Check the result**

Run Step 5's command again.
Expected: the tech line reads `Python, NumPy, SciPy, NetworkX, rasterio, Shapely, pyosmium, OpenStreetMap, WorldPop, DOSM data, Next.js` and ends before x = 562; the bullet starts `Road distance from every populated 100 m cell in Penang` and its percentages and facility count equal `keyNumbers[0].value`, `keyNumbers[1].value` and `keyNumbers[2].value` in `penang-pulse.json`; no line passes x = 562; the Forecasting Lab lines are unchanged; nothing below has moved.

Open the `*-before.png` and `*-after.png` renders in `.context/resume/` side by side: same margins and baselines, the bullet glyph intact, no overlap with the tech line or the Forecasting Lab heading.

Run: `git check-ignore -v ".context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf"`
Expected: one line naming the ignore rule. If it prints nothing, do not commit anything from `.context/` and add `.context/` to `.git/info/exclude` first.

- [ ] **Step 8: Commit**

```bash
git add analysis/tools/update_cv.py analysis/tests/test_update_cv.py apps/web/public/subashanan-nair-cv.pdf
git commit -m "feat: update the CV from the Penang Pulse results"
```

- [ ] **Step 9: Run every check**

Run from the root: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`. Then in `analysis/`: `uv sync --locked` and `uv run pytest`.
Expected: `Tests  145 passed (145)`, no lint or type errors, a successful build, and `124 passed`. Restore `apps/web/next-env.d.ts` afterwards with `git checkout -- apps/web/next-env.d.ts`.

- [ ] **Step 10: Check what the branch adds**

Run: `git diff --stat main...HEAD` and `git diff main...HEAD --name-only | grep -E "data/raw|\.venv|\.env|\.vercel|\.context|\.superpowers|next-env|\.pbf$|\.tif$|\.zip$|\.parquet$"`.
Expected: the files in the file map only, and no output from the grep.

- [ ] **Step 11: Open the pull request**

Write the body to `/tmp/pp-pr-body.md` with these sections: **Summary** (the pipeline, road distance from every populated cell, the published results, the table, the CV update); **Results for approval** (paste the `answer`, the three key numbers and each district's bands and `far` values from `penang-pulse.json` verbatim, and ask Subashanan to approve the wording); **Decisions** (spec section 14, plus this plan's: rounding and ties as in Task 8; bridges drawn only over water; the hand-set George Town and Butterworth label nudge; swapped or zero facility coordinates stop the run; the CV tool is safe to rerun; the Penang Pulse CV tech line swap); **Data findings** (the facility counts and the four facilities outside every district polygon, the Geofabrik extract date, cell counts per district for both maps, any GTFS checksum drift, from the manifest); **Test plan** as checkboxes: web tests, lint, typecheck and build; `uv run pytest`; the bad-file build check; the screenshots; the CV before and after renders.

```bash
git push -u origin penang-pulse-pipeline
gh pr create --base main --title "feat: publish real Penang Pulse results" --body-file /tmp/pp-pr-body.md
```

Expected: `gh` prints the pull request URL. CI runs both jobs, `quality` and `analysis`, and both pass.
