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
