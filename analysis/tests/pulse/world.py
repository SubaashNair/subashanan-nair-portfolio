"""A tiny synthetic Penang: five rectangular districts on an island and a mainland with a strait between, and the files the loaders read."""

from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import MultiPolygon, box, mapping

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
