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
# a label is about 160 px wide in map units on a phone, so centred labels would overlap. Replace with label collision
# handling if more labels are added.
LABEL_NUDGE_PX = {"George Town": (-70.0, 0.0), "Butterworth": (66.0, 0.0)}


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
