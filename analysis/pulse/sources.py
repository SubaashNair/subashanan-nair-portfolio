"""Where each Penang Pulse input comes from, and a cached, checksummed download of each file."""

from __future__ import annotations

import logging
import re
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from forecasting.data import sha256_of

log = logging.getLogger(__name__)

USER_AGENT = "observatory-analysis/0.1 (Penang Pulse study)"
CHECKED_ON = "2026-10-14"


@dataclass(frozen=True)
class Source:
    name: str  # the name the study page lists, and the key in the results file's `retrieved`
    file: str  # cache file name in the raw directory
    url: str
    licence: str
    sha256: str  # as checked on CHECKED_ON
    fixed: bool  # False for files the publisher overwrites in place: a different checksum is then logged, not fatal


HEALTH = Source(
    "Public health facilities 2022",
    "pusat_kesihatan_awam_2022_p.csv",
    "https://archive.data.gov.my/data/dataset/20a4c459-5329-450a-8cad-938957f2eefe/resource/95ed70e3-955f-43a8-a99d-072accc49ed0/download/_202310251223490_pusat_kesihatan_awam_2022_p.csv",
    "CC BY",
    "30d7abe179258b20944c775605d9a466bfb8f92c519e5f586d52961848742f68",
    True,
)
SCHOOLS = Source(
    "Schools 2022",
    "be0010_sekolah_2022_p.csv",
    "https://archive.data.gov.my/data/dataset/13d6b29c-2460-4f3e-ba6e-5fb58e407e15/resource/0566082a-6a70-4f2e-9f8c-bd587d2f8cb0/download/_202310251214180_be0010_sekolah_2022_p.csv",
    "CC BY",
    "dc84127ba313d11d0fe70b2ae8f6d70221dbede4077a90f0b2c843fd483e734e",
    True,
)
GTFS = Source(
    "Rapid Penang GTFS",
    "rapid_bus_penang_gtfs.zip",
    "https://api.data.gov.my/gtfs-static/prasarana?category=rapid-bus-penang",
    "CC BY 4.0",
    "9823a7c793108805560a826070ca9c89089c685f9d28c8869337b425aa669c73",
    False,
)
DOSM = Source(
    "Population by district",
    "population_district.parquet",
    "https://storage.dosm.gov.my/population/population_district.parquet",
    "CC BY 4.0",
    "456bca234306c740c523753c62630d409c8713c82cd94b596074a7ca3a024742",
    True,
)
BOUNDARIES = Source(
    "geoBoundaries MYS ADM2",
    "geoBoundaries-MYS-ADM2.geojson",
    "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/9469f09592ced973a3448cf66b6100b741b64c0d/releaseData/gbOpen/MYS/ADM2/geoBoundaries-MYS-ADM2.geojson",
    "CC BY 3.0",
    "1a7db3b44563073171b02eba59b109fc1bc6256ab0b011531ea6d5053515e550",
    True,
)
WORLDPOP = Source(
    "WorldPop 2020 constrained",
    "mys_ppp_2020_UNadj_constrained.tif",
    "https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/MYS/mys_ppp_2020_UNadj_constrained.tif",
    "CC BY 4.0",
    "b54a9a075af3d0964794af77d958d679aebbd01c4b2a340f3fdef0a287de981c",
    True,
)
META = Source(
    "Meta population map 2020",
    "mys_general_2020_geotiff.zip",
    "https://data.humdata.org/dataset/f165a732-7125-4321-baad-1b7005ed93d0/resource/e8e63524-9f06-486a-afd8-cbf752073d08/download/mys_general_2020_geotiff.zip",
    "CC BY",
    "31317c66c4d6506267c432cfa7161d3b2927b4adbf6760bad66931581da9250f",
    True,
)
FILE_SOURCES = (HEALTH, SCHOOLS, GTFS, DOSM, BOUNDARIES, WORLDPOP, META)
META_MEMBER = "mys_general_2020.tif"  # the one GeoTIFF inside the Meta zip, about 17.4 GB uncompressed

OSM_NAME = "OpenStreetMap"
OSM_LICENCE = "ODbL"
GEOFABRIK_DIR = "https://download.geofabrik.de/asia/"
GEOFABRIK_LATEST = GEOFABRIK_DIR + "malaysia-singapore-brunei-latest.osm.pbf"  # redirects to the dated file
GEOFABRIK_FILE = re.compile(r"^malaysia-singapore-brunei-(\d{2})(\d{2})(\d{2})\.osm\.pbf$")


@dataclass(frozen=True)
class Fetched:
    name: str
    url: str
    licence: str
    path: Path
    retrieved: str  # ISO 8601 timestamp, UTC
    bytes: int
    sha256: str


def download(url: str, path: Path) -> None:
    """Stream url to path through a partial file, so an interrupted download never looks complete."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response, partial.open("wb") as out:
        shutil.copyfileobj(response, out, 1 << 20)
    partial.replace(path)


def retrieved_at(path: Path) -> str:
    """When this cached file was downloaded, recorded beside it on first sight."""
    stamp = path.with_name(path.name + ".retrieved")
    if not stamp.exists():
        stamp.write_text(datetime.now(UTC).replace(microsecond=0).isoformat())
    return stamp.read_text().strip()


def fetch(source: Source, raw_dir: Path) -> Fetched:
    """Download once into raw_dir, then reuse the cache. A changed checksum stops the run for a fixed source."""
    path = raw_dir / source.file
    if not path.exists():
        log.info("downloading %s", source.name)
        download(source.url, path)
    digest = sha256_of(path)
    if digest != source.sha256:
        message = f"{source.name}: SHA-256 {digest} differs from {source.sha256}, checked on {CHECKED_ON}"
        if source.fixed:
            raise ValueError(message)
        log.warning(message)
    return Fetched(source.name, source.url, source.licence, path, retrieved_at(path), path.stat().st_size, digest)


def geofabrik_date(file_name: str) -> str:
    """The data date in a dated Geofabrik file name, as YYYY-MM-DD."""
    match = GEOFABRIK_FILE.match(file_name)
    if match is None:
        raise ValueError(f"{file_name!r} is not a dated malaysia-singapore-brunei .osm.pbf file")
    yy, mm, dd = match.groups()
    return f"20{yy}-{mm}-{dd}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def latest_geofabrik_url() -> str:
    """Ask Geofabrik which dated file `-latest` points at today, without downloading it."""
    request = urllib.request.Request(GEOFABRIK_LATEST, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=60) as response:
            return response.url
    except urllib.error.HTTPError as err:
        if err.code in (301, 302, 303, 307, 308):
            return str(err.headers["Location"])
        raise


def fetch_osm(raw_dir: Path) -> Fetched:
    """Reuse the newest cached dated extract, so a rerun uses the same roads; otherwise download today's."""
    cached = sorted(p for p in raw_dir.glob("malaysia-singapore-brunei-*.osm.pbf") if GEOFABRIK_FILE.match(p.name))
    if cached:
        path = cached[-1]
    else:
        url = latest_geofabrik_url()
        path = raw_dir / url.rsplit("/", 1)[-1]
        geofabrik_date(path.name)  # refuse anything that is not a dated extract
        log.info("downloading %s (about 250 MB)", path.name)
        download(url, path)
    return Fetched(OSM_NAME, GEOFABRIK_DIR + path.name, OSM_LICENCE, path, retrieved_at(path), path.stat().st_size, sha256_of(path))
