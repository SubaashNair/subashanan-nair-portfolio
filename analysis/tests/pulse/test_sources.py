import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path

import pytest

from pulse import sources
from pulse.sources import FILE_SOURCES, Source, fetch, fetch_osm, geofabrik_date


def local_source(tmp_path: Path, content: bytes = b"abc", sha256: str | None = None, fixed: bool = True) -> Source:
    origin = tmp_path / "origin.csv"
    origin.write_bytes(content)
    return Source("Test source", "test.csv", origin.as_uri(), "CC BY", sha256 or hashlib.sha256(content).hexdigest(), fixed)


def test_fetch_downloads_once_and_records_when(tmp_path: Path) -> None:
    source = local_source(tmp_path)
    first = fetch(source, tmp_path / "raw")
    (tmp_path / "origin.csv").unlink()  # the second fetch must use the cache
    second = fetch(source, tmp_path / "raw")

    assert first == second
    assert first.path == tmp_path / "raw/test.csv"
    assert (first.bytes, first.sha256) == (3, hashlib.sha256(b"abc").hexdigest())
    assert datetime.fromisoformat(first.retrieved).utcoffset() is not None
    assert not list((tmp_path / "raw").glob("*.part"))


def test_a_changed_fixed_source_stops_the_run(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Test source: SHA-256 .* differs from 0{64}"):
        fetch(local_source(tmp_path, sha256="0" * 64), tmp_path / "raw")


def test_a_changed_feed_is_logged_and_used(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        fetched = fetch(local_source(tmp_path, sha256="0" * 64, fixed=False), tmp_path / "raw")
    assert "differs from" in caplog.text
    assert fetched.bytes == 3


def test_geofabrik_dates_come_from_the_file_name() -> None:
    assert geofabrik_date("malaysia-singapore-brunei-261013.osm.pbf") == "2026-10-13"
    with pytest.raises(ValueError, match="not a dated"):
        geofabrik_date("malaysia-singapore-brunei-latest.osm.pbf")


def test_the_newest_cached_extract_is_reused_without_asking_geofabrik(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "malaysia-singapore-brunei-261001.osm.pbf").write_bytes(b"old")
    (tmp_path / "malaysia-singapore-brunei-261013.osm.pbf").write_bytes(b"new")
    monkeypatch.setattr(sources, "latest_geofabrik_url", lambda: pytest.fail("asked Geofabrik"))

    fetched = fetch_osm(tmp_path)

    assert fetched.path.name == "malaysia-singapore-brunei-261013.osm.pbf"
    assert fetched.url == "https://download.geofabrik.de/asia/malaysia-singapore-brunei-261013.osm.pbf"
    assert (fetched.name, fetched.licence, fetched.bytes) == ("OpenStreetMap", "ODbL", 3)


def test_every_source_has_a_full_checksum_and_its_own_file() -> None:
    assert all(re.fullmatch(r"[0-9a-f]{64}", s.sha256) for s in FILE_SOURCES)
    assert [s.name for s in FILE_SOURCES if not s.fixed] == ["Rapid Penang GTFS"]
    assert len({s.file for s in FILE_SOURCES}) == len(FILE_SOURCES)
