"""Read the Geofabrik extract: the drivable road graph around Penang, the two bridges and six town labels."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import osmium

from .load import Bounds, inside

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
