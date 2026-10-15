import re
from pathlib import Path

import numpy as np
import pytest

from pulse.distance import LAT0
from pulse.geometry import MARGIN_PX, VIEW_H, VIEW_W, fit, map_geometry, points_json, project
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
