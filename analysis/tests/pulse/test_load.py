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
