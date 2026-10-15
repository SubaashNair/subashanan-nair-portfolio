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
