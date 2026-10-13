import json
from pathlib import Path

from forecasting.chronos_adapter import CHRONOS_REVISION
from forecasting.cli import build_manifest
from forecasting.data import SOURCE_URL, RawFiles, make_split, sha256_of
from forecasting.pipeline import RunResult


def test_manifest_records_the_provenance_of_a_run(tmp_path: Path, tiny_run: RunResult) -> None:
    (tmp_path / "data.zip").write_bytes(b"zip bytes")
    (tmp_path / "data.mat").write_bytes(b"mat bytes")
    raw = RawFiles(zip_path=tmp_path / "data.zip", mat_path=tmp_path / "data.mat", retrieved="2026-10-13T01:02:03+00:00")
    manifest = build_manifest(raw, make_split(1100), tiny_run, 42, {"python": "3.12.9"}, {"commit": "abc1234", "dirty": False})

    assert manifest["source"]["url"] == SOURCE_URL
    assert manifest["source"]["retrieved"] == "2026-10-13T01:02:03+00:00"
    assert manifest["source"]["zip_sha256"] == sha256_of(tmp_path / "data.zip")
    assert manifest["source"]["mat_sha256"] == sha256_of(tmp_path / "data.mat")
    assert manifest["split"] == {"train": [0, 864], "val": [864, 1056], "test": [1056, 1100]}
    assert manifest["seeds"] == {"models": 42, "bootstrap": 42, "torch": 42}
    assert manifest["chronos"]["revision"] == CHRONOS_REVISION
    assert manifest["packages"] == {"python": "3.12.9"}
    assert manifest["git"] == {"commit": "abc1234", "dirty": False}
    assert manifest["results_file"] == "apps/web/src/content/results/forecasting-lab.json"
    assert sorted(manifest["tuning"]) == ["gb", "mlp"]
    json.dumps(manifest)  # serialisable as written
