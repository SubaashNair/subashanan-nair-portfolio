"""Road distance from each populated cell to the nearest facility, and the share of residents in each distance band."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

from .roads import EARTH_RADIUS_M

LON0, LAT0 = 100.35, 5.35  # Penang's centre, for a local equirectangular projection in metres
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
