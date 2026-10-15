"""Read the facility CSVs, the GTFS stops, the district outlines and the DOSM district totals."""

from __future__ import annotations

import csv
import datetime
import io
import json
import math
import re
import zipfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq
import shapely
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

Bounds = tuple[float, float, float, float]  # min lon, min lat, max lon, max lat


@dataclass(frozen=True)
class DistrictSpec:
    id: str
    name: str  # as spelled by both DOSM and geoBoundaries
    short: str
    land: str  # "island" or "mainland"


DISTRICTS = (
    DistrictSpec("tl", "Timur Laut", "Timur Laut", "island"),
    DistrictSpec("bd", "Barat Daya", "Barat Daya", "island"),
    DistrictSpec("spu", "Seberang Perai Utara", "SP Utara", "mainland"),
    DistrictSpec("spt", "Seberang Perai Tengah", "SP Tengah", "mainland"),
    DistrictSpec("sps", "Seberang Perai Selatan", "SP Selatan", "mainland"),
)
CATEGORIES = ("clinic", "school", "transit")
DENTAL = "KLINIK PERGIGIAN"
AREA_MARGIN_DEG = 0.1  # about 11 km: a facility further than this outside the districts' box has bad coordinates
DOSM_FILTER = {"state": "Pulau Pinang", "sex": "both", "age": "overall", "ethnicity": "overall"}
DOSM_DATE = datetime.date(2020, 1, 1)
DATE = re.compile(r"^\d{2}/\d{2}/(\d{4})$")


@dataclass(frozen=True)
class Facility:
    category: str
    lon: float
    lat: float
    year: int | None  # the record's TARIKH_DATA year; None for GTFS stops


def expand(bounds: Bounds, margin: float) -> Bounds:
    return (bounds[0] - margin, bounds[1] - margin, bounds[2] + margin, bounds[3] + margin)


def inside(bounds: Bounds, lon: float, lat: float) -> bool:
    return bounds[0] <= lon <= bounds[2] and bounds[1] <= lat <= bounds[3]


def read_rows(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    """CSV rows as dicts. utf-8-sig drops the byte order mark the state files start with, and is harmless without one."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name} is missing columns {missing}")
        return list(reader)


def parse_point(x: str, y: str, where: str) -> tuple[float, float]:
    """Longitude and latitude, failing on anything missing or non-numeric."""
    try:
        lon, lat = float(x), float(y)
    except ValueError:
        raise ValueError(f"{where}: bad coordinates X={x!r} Y={y!r}") from None
    if not (math.isfinite(lon) and math.isfinite(lat)):
        raise ValueError(f"{where}: bad coordinates X={x!r} Y={y!r}")
    return lon, lat


def data_year(value: str, where: str) -> int:
    match = DATE.match(value.strip())
    if match is None:
        raise ValueError(f"{where}: TARIKH_DATA {value!r} is not DD/MM/YYYY")
    return int(match.group(1))


def read_facilities(path: Path, category: str, area: Bounds, keep: Callable[[dict[str, str]], bool], extra: tuple[str, ...] = ()) -> list[Facility]:
    """Rows that pass keep, as facilities. A point outside area (for example X and Y swapped) is a bad coordinate."""
    facilities = []
    for line, row in enumerate(read_rows(path, ("X", "Y", "TARIKH_DATA", *extra)), start=2):  # line 1 is the header
        if not keep(row):
            continue
        where = f"{path.name} line {line}"
        lon, lat = parse_point(row["X"], row["Y"], where)
        if not inside(area, lon, lat):
            raise ValueError(f"{where}: coordinates X={row['X']!r} Y={row['Y']!r} are not in the Penang area")
        facilities.append(Facility(category, lon, lat, data_year(row["TARIKH_DATA"], where)))
    return facilities


def read_clinics(path: Path, area: Bounds) -> list[Facility]:
    """Every public health facility except dental clinics."""
    return read_facilities(path, "clinic", area, lambda row: row["JENIS"] != DENTAL, extra=("JENIS",))


def read_schools(path: Path, area: Bounds) -> list[Facility]:
    """Every school, private ones included."""
    return read_facilities(path, "school", area, lambda row: True)


def read_stops(gtfs_zip: Path, land: BaseGeometry) -> list[Facility]:
    """Rapid Penang stops inside the five districts. Stops elsewhere on the network are left out."""
    with zipfile.ZipFile(gtfs_zip) as archive, archive.open("stops.txt") as raw:
        rows = list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig")))
    points = [parse_point(r["stop_lon"], r["stop_lat"], f"stops.txt line {i}") for i, r in enumerate(rows, start=2)]
    return [Facility("transit", lon, lat, None) for lon, lat in points if shapely.contains_xy(land, lon, lat)]


def load_districts(path: Path) -> list[BaseGeometry]:
    """The five district outlines from geoBoundaries ADM2, in DISTRICTS order, selected by name."""
    features = json.loads(path.read_text())["features"]
    found = {f["properties"]["shapeName"]: shape(f["geometry"]) for f in features}
    missing = [d.name for d in DISTRICTS if d.name not in found]
    if missing:
        raise ValueError(f"{path.name} has no district named {missing}")
    return [found[d.name] for d in DISTRICTS]


def load_totals(path: Path) -> list[int]:
    """DOSM 2020 population per district, in people, in DISTRICTS order. The file stores thousands."""
    condition = pc.field("date") == DOSM_DATE
    for column, value in DOSM_FILTER.items():
        condition = condition & (pc.field(column) == value)
    rows = pq.read_table(path, columns=["district", "population"], filters=condition).to_pylist()
    totals: dict[str, int] = {}
    for row in rows:
        if row["district"] in totals:
            raise ValueError(f"{path.name} has more than one 2020 total for {row['district']}")
        totals[row["district"]] = round(row["population"] * 1000)
    missing = [d.name for d in DISTRICTS if d.name not in totals]
    if missing:
        raise ValueError(f"{path.name} has no 2020 total for {missing}")
    return [totals[d.name] for d in DISTRICTS]


def outside_districts(facilities: list[Facility], land: BaseGeometry) -> dict[str, int]:
    """How many facilities of each category lie outside every district. They are kept, and logged by the caller."""
    counts = Counter(f.category for f in facilities if not shapely.contains_xy(land, f.lon, f.lat))
    return {c: counts[c] for c in CATEGORIES}
