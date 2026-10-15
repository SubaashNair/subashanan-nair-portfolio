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
