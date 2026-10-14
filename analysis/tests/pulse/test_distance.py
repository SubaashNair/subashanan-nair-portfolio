import networkx as nx
import numpy as np
import pytest

from pulse.distance import band_shares, cell_distances, largest_remainder, network_from, road_index, snap, to_metres
from pulse.roads import Way, build_graph, haversine


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
    # A school sits next to a small disconnected fragment of road. The pipeline keeps only the largest component,
    # so the school must snap to the nearest node of the main network and still be reachable from it.
    main = Way(frozenset(), tuple((n, *STRAIT[n]) for n in STRAIT))
    fragment = Way(frozenset(), ((11, 100.24, 5.31), (12, 100.2405, 5.31)))
    graph, dropped = build_graph([main, fragment])
    assert dropped == 2 and 11 not in graph
    index = road_index(graph)
    school, cell = (100.2405, 5.3105), STRAIT[1]  # the school's nearest raw road node is 12; node 4 is the nearest on the main network
    snapped = snap(index, np.array([school[0]]), np.array([school[1]]))
    assert snapped.node.tolist() == [4]
    got = cell_distances(network_from(graph, snapped), snap(index, np.array([cell[0]]), np.array([cell[1]])))
    network = sum(graph.edges[e]["weight"] for e in [(1, 2), (2, 3), (3, 4)])
    assert got[0] == pytest.approx(metres_between(school, STRAIT[4]) + network)


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
