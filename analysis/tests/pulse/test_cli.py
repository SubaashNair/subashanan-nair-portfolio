import json
from pathlib import Path

from pulse.cli import build_manifest
from pulse.pipeline import PulseRun
from pulse.sources import Fetched


def fetched(tmp_path: Path, name: str, file: str) -> Fetched:
    path = tmp_path / file
    path.write_bytes(b"x")
    return Fetched(name, f"https://example.org/{file}", "CC BY", path, "2026-10-14T01:02:03+00:00", 1, "ab" * 32)


def test_manifest_records_the_provenance_of_a_run(tmp_path: Path, pulse_run: PulseRun) -> None:
    sources = [fetched(tmp_path, "Schools 2022", "schools.csv"), fetched(tmp_path, "OpenStreetMap", "malaysia-singapore-brunei-261013.osm.pbf")]
    manifest = build_manifest(sources, pulse_run, {"python": "3.12.9"}, {"commit": "abc1234", "dirty": False})

    assert manifest["sources"][0] == {
        "name": "Schools 2022",
        "url": "https://example.org/schools.csv",
        "licence": "CC BY",
        "retrieved": "2026-10-14T01:02:03+00:00",
        "bytes": 1,
        "sha256": "ab" * 32,
    }
    assert manifest["geofabrik_date"] == "2026-10-13"
    assert manifest["facilities"] == {"used": {"clinic": 3, "school": 3, "transit": 2}, "outside_districts": {"clinic": 1, "school": 0, "transit": 0}, "years": [2013, 2022]}
    assert manifest["roads"] == {"nodes": 14, "edges": 14, "dropped_nodes": 2}
    assert manifest["cells"]["meta"] == {"tl": 5, "bd": 6, "spu": 6, "spt": 6, "sps": 6}
    assert sorted(manifest["shares_percent"]) == ["meta", "worldpop"]
    assert len(manifest["shares_percent"]["worldpop"]["sps"]["school"]) == 3
    assert manifest["band_edges_m"] == [1000.0, 3000.0]
    assert manifest["git"] == {"commit": "abc1234", "dirty": False}
    assert manifest["results_file"] == "apps/web/src/content/results/penang-pulse.json"
    json.dumps(manifest, allow_nan=False)
