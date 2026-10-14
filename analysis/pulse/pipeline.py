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


def collect_facilities(inputs: Inputs, land: BaseGeometry) -> list[Facility]:
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
    used = collect_facilities(inputs, land)
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
