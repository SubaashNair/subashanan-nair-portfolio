"""A tiny synthetic Penang: five rectangular districts on an island and a mainland with a strait between, and the files the loaders read."""

from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import MultiPolygon, box, mapping

from pulse.pipeline import Inputs
from pulse.population import meta_path
from pulse.sources import META_MEMBER

BOXES = {  # min lon, min lat, max lon, max lat
    "Timur Laut": (100.20, 5.33, 100.22, 5.36),
    "Barat Daya": (100.20, 5.30, 100.22, 5.33),
    "Seberang Perai Utara": (100.23, 5.34, 100.26, 5.36),
    "Seberang Perai Tengah": (100.23, 5.32, 100.26, 5.34),
    "Seberang Perai Selatan": (100.23, 5.30, 100.26, 5.32),
}
ISLET = (100.222, 5.300, 100.224, 5.302)  # a small island in the strait that belongs to Timur Laut, so one district is a MultiPolygon
DECOY = ("Kuala Muda", (100.40, 5.60, 100.42, 5.62))  # a district in another state, which must be ignored
THOUSANDS = {"Timur Laut": 6.0, "Barat Daya": 3.0, "Seberang Perai Utara": 4.0, "Seberang Perai Tengah": 4.5, "Seberang Perai Selatan": 2.5}
AREA = (100.10, 5.20, 100.36, 5.46)  # the districts' box widened by AREA_MARGIN_DEG

HEALTH_HEADER = ["NAMA", "NO_TEL", "NO_FAKS", "JENIS", "TARIKH_DATA", "NO", "UNIT_TKT", "BANGUNAN", "JALAN", "KG_TMN", "BANDAR", "POSKOD", "DAERAH", "NEGERI", "X", "Y"]
CLINICS = [  # NAMA, JENIS, TARIKH_DATA, DAERAH, X, Y
    ("KLINIK KESIHATAN UTARA", "KLINIK KESIHATAN", "17/02/2021", "SPU", "100.245", "5.355"),
    ("KLINIK DESA BARAT", "KLINIK DESA", "31/12/2013", "DBD", "100.21", "5.305"),
    ("KLINIK PERGIGIAN TIMUR", "KLINIK PERGIGIAN", "01/06/2022", "DTL", "100.21", "5.355"),  # dental, left out
    ("HOSPITAL SEBERANG", "HOSPITAL KERAJAAN", "31/12/2022", "SPS", "100.265", "5.31"),  # just outside every district, kept
]
SCHOOL_HEADER = ["NAM", "TEL", "FAX", "EML", "WEB", "PPD", "KATEGORI", "TARIKH_DATA", "PERINGKAT", "JENIS_LABEL", "ALAMATSURAT", "LOKASI", "JENIS_BANTUAN",
                 "PRASEKOLAH", "INTEGRASI", "NAM_LABEL", "UNIT_TKT", "BANGUNAN", "JALAN", "KG_TMN", "BANDAR", "POSKOD", "DAERAH", "NEGERI", "ID_SKLH", "X", "Y"]
SCHOOLS = [  # NAM, PERINGKAT, JENIS_LABEL, TARIKH_DATA, DAERAH, X, Y
    ("SK TIMUR", "RENDAH", "SK", "31/12/2015", "DTL", "100.215", "5.345"),
    ("SMK TENGAH", "MENENGAH", "SMK", "31/12/2020", "SPT", "100.25", "5.325"),
    ("SEKOLAH SWASTA SELATAN", "TIADA", "SWASTA", "31/12/2018", "SPS", "100.24", "5.305"),
]
STOPS = [("1", "5.325", "100.21"), ("2", "5.335", "100.245"), ("3", "5.40", "100.30")]  # stop_id, stop_lat, stop_lon; the third is outside


def write_csv(path: Path, header: list[str], rows: list[dict[str, str]], encoding: str = "utf-8-sig") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, restval="NA")
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_health(folder: Path, clinics: list[tuple[str, ...]] = CLINICS, encoding: str = "utf-8-sig") -> Path:
    rows = [{"NAMA": n, "JENIS": j, "TARIKH_DATA": t, "DAERAH": d, "NEGERI": "PULAU PINANG", "X": x, "Y": y} for n, j, t, d, x, y in clinics]
    return write_csv(folder / "health.csv", HEALTH_HEADER, rows, encoding)


def write_schools(folder: Path, schools: list[tuple[str, ...]] = SCHOOLS) -> Path:
    rows = [{"NAM": n, "PERINGKAT": p, "JENIS_LABEL": j, "TARIKH_DATA": t, "DAERAH": d, "NEGERI": "PULAU PINANG", "X": x, "Y": y} for n, p, j, t, d, x, y in schools]
    return write_csv(folder / "schools.csv", SCHOOL_HEADER, rows)


def write_gtfs(folder: Path, stops: list[tuple[str, str, str]] = STOPS) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["stop_id,stop_code,stop_name,stop_lat,stop_lon", *(f"{i},S{i},Stop {i},{lat},{lon}" for i, lat, lon in stops)]
    path = folder / "gtfs.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("stops.txt", "\n".join(lines) + "\n")
    return path


def district_shapes() -> dict[str, object]:
    shapes: dict[str, object] = {name: box(*bounds) for name, bounds in BOXES.items()}
    return {**shapes, "Timur Laut": MultiPolygon([box(*BOXES["Timur Laut"]), box(*ISLET)])}


def write_boundaries(folder: Path, names: list[str] | None = None) -> Path:
    shapes = district_shapes()
    chosen = list(BOXES) if names is None else names
    features = [{"type": "Feature", "properties": {"shapeName": n, "shapeType": "ADM2"}, "geometry": mapping(shapes[n])} for n in chosen]
    features.append({"type": "Feature", "properties": {"shapeName": DECOY[0], "shapeType": "ADM2"}, "geometry": mapping(box(*DECOY[1]))})
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "boundaries.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return path


def write_dosm(folder: Path, thousands: dict[str, float] = THOUSANDS, extra: list[dict[str, object]] | None = None) -> Path:
    def row(district: str, population: float, **changes: object) -> dict[str, object]:
        base = {"state": "Pulau Pinang", "district": district, "date": datetime.date(2020, 1, 1), "sex": "both", "age": "overall", "ethnicity": "overall"}
        return {**base, "population": population, **changes}

    rows = [row(d, p) for d, p in thousands.items()]
    decoys = [row("Timur Laut", 9.9, date=datetime.date(2021, 1, 1)), row("Timur Laut", 3.1, sex="male"), row("Kuala Muda", 7.0, state="Kedah")]
    columns = {k: [r[k] for r in [*rows, *decoys, *(extra or [])]] for k in rows[0]}
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "population_district.parquet"
    pq.write_table(pa.table(columns), path)
    return path


GRID_ORIGIN = (100.20, 5.36)  # top left corner of the population grid
GRID_STEP = 0.01  # degrees per cell, so cell centres sit at 100.205, 100.215, ...
LAND_COLUMNS = (0, 1, 3, 4, 5)  # column 2 is the strait
NODATA_CELL = (0, 0)  # one Timur Laut cell with no data


def population_grid(value: float, nodata: float) -> np.ndarray:
    grid = np.zeros((6, 6))
    grid[:, list(LAND_COLUMNS)] = value
    grid[NODATA_CELL] = nodata
    return grid


def write_raster(path: Path, grid: np.ndarray, dtype: str, nodata: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    transform = from_origin(*GRID_ORIGIN, GRID_STEP, GRID_STEP)
    with rasterio.open(path, "w", driver="GTiff", width=6, height=6, count=1, dtype=dtype, crs="EPSG:4326", transform=transform, nodata=nodata) as dst:
        dst.write(grid.astype(dtype), 1)
    return path


def write_worldpop(folder: Path) -> Path:
    """WorldPop style: float32 with -99999 for nodata."""
    return write_raster(folder / "worldpop.tif", population_grid(10.0, -99999.0), "float32", -99999.0)


def write_meta(folder: Path) -> Path:
    """Meta style: a float64 GeoTIFF with NaN for nodata, zipped under the real member name."""
    tif = write_raster(folder / "meta.tif", population_grid(20.0, np.nan), "float64", np.nan)
    path = folder / "meta.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(tif, META_MEMBER)
    tif.unlink()
    return path


OSM_NODES = {  # id: (lon, lat)
    **{i: (100.21, 5.295 + 0.01 * i) for i in range(1, 7)},  # island street, 5.305 to 5.355
    **{10 + i: (100.245, 5.295 + 0.01 * i) for i in range(1, 7)},  # mainland street
    21: (100.2275, 5.335),  # mid-strait point of the Penang Bridge
    22: (100.2275, 5.305),  # mid-strait point of the second bridge
    31: (100.255, 5.355), 32: (100.256, 5.355),  # a fragment joined to nothing
    51: (101.50, 5.50), 52: (101.51, 5.50),  # a road far outside the Penang box
    41: (100.21, 5.355), 42: (100.21, 5.305), 43: (100.205, 5.32), 44: (100.24, 5.355), 45: (100.255, 5.33), 46: (100.25, 5.305),
    47: (100.215, 5.31),  # a neighbourhood that shares the name Bayan Lepas
}
OSM_WAYS = [  # id, node ids, tags
    (101, [1, 2, 3, 4, 5, 6], {"highway": "residential", "name": "Jalan Pulau"}),
    (102, [11, 12, 13, 14, 15, 16], {"highway": "primary", "name": "Jalan Tanah Besar"}),
    (103, [4, 21, 14], {"highway": "motorway", "bridge": "yes", "name": "Jambatan Pulau Pinang", "name:en": "Penang Bridge"}),
    (104, [1, 22, 11], {"highway": "motorway", "bridge": "yes", "name": "Jambatan Sultan Abdul Halim Mu'adzam Shah"}),
    (105, [6, 16], {"highway": "footway"}),  # footpaths are not roads
    (106, [5, 15], {"highway": "service", "access": "private"}),  # neither are private roads
    (107, [3, 13], {"route": "ferry"}),  # nor ferries
    (108, [31, 32], {"highway": "residential"}),
    (109, [51, 52], {"highway": "residential"}),
]
OSM_PLACES = {  # node id: tags
    41: {"place": "city", "name": "George Town"},
    42: {"place": "town", "name": "Bayan Lepas"},
    43: {"place": "town", "name": "Balik Pulau"},
    44: {"place": "city", "name": "Butterworth"},
    45: {"place": "city", "name": "Bukit Mertajam"},
    46: {"place": "town", "name": "Nibong Tebal"},
    47: {"place": "neighbourhood", "name": "Bayan Lepas"},
}
OSM_BBOX = (100.15, 5.25, 100.31, 5.41)  # the districts' box widened by ROAD_MARGIN_DEG


def tag_xml(tags: dict[str, str]) -> str:
    return "".join(f"<tag k={quoteattr(k)} v={quoteattr(v)}/>" for k, v in tags.items())


def write_osm(folder: Path, ways: list[tuple[int, list[int], dict[str, str]]] = OSM_WAYS, places: dict[int, dict[str, str]] = OSM_PLACES) -> Path:
    """An .osm XML file. pyosmium reads it exactly as it reads the real .osm.pbf."""
    nodes = [f'<node id="{i}" version="1" lat="{lat}" lon="{lon}">{tag_xml(places.get(i, {}))}</node>' for i, (lon, lat) in OSM_NODES.items()]
    way_xml = [f'<way id="{i}" version="1">' + "".join(f'<nd ref="{n}"/>' for n in refs) + f"{tag_xml(tags)}</way>" for i, refs, tags in ways]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "penang.osm"
    path.write_text("<?xml version='1.0' encoding='UTF-8'?>\n<osm version=\"0.6\">\n" + "\n".join([*nodes, *way_xml]) + "\n</osm>\n")
    return path


def write_inputs(folder: Path) -> Inputs:
    """Every input file of the synthetic world, as the pipeline takes them."""
    return Inputs(
        health=write_health(folder),
        schools=write_schools(folder),
        gtfs=write_gtfs(folder),
        dosm=write_dosm(folder),
        boundaries=write_boundaries(folder),
        worldpop=str(write_worldpop(folder)),
        meta=meta_path(write_meta(folder)),
        osm=write_osm(folder),
    )
