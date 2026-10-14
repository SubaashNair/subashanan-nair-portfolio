"""Entry point: python -m pulse.cli (run from analysis/). Downloads every source, runs the study and writes its results."""

from __future__ import annotations

import argparse
import logging
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from forecasting.cli import git_state
from forecasting.export import write_json

from .distance import BAND_EDGES_M
from .export import build_results, shares_json
from .load import DISTRICTS
from .pipeline import Inputs, PulseRun, run
from .population import meta_path
from .sources import BOUNDARIES, DOSM, FILE_SOURCES, GTFS, HEALTH, META, OSM_NAME, SCHOOLS, WORLDPOP, Fetched, fetch, fetch_osm, geofabrik_date

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ANALYSIS_DIR.parent
RESULTS_PATH = REPO_DIR / "apps/web/src/content/results/penang-pulse.json"
MANIFEST_PATH = ANALYSIS_DIR / "outputs/penang-pulse-manifest.json"
LIBRARIES = ("numpy", "scipy", "networkx", "osmium", "pyarrow", "rasterio", "shapely")


def build_manifest(fetched: list[Fetched], result: PulseRun, packages: dict[str, str], git: dict[str, Any]) -> dict[str, Any]:
    osm = next(f for f in fetched if f.name == OSM_NAME)
    return {
        "study": "penang-pulse",
        "sources": [{"name": f.name, "url": f.url, "licence": f.licence, "retrieved": f.retrieved, "bytes": f.bytes, "sha256": f.sha256} for f in fetched],
        "geofabrik_date": geofabrik_date(osm.path.name),
        "facilities": {"used": result.findings.counts, "outside_districts": result.outside, "years": list(result.findings.years)},
        "roads": result.roads,
        "cells": {name: dict(zip([d.id for d in DISTRICTS], counts, strict=True)) for name, counts in result.cells.items()},
        "band_edges_m": list(BAND_EDGES_M),
        "shares_percent": {name: shares_json(shares) for name, shares in result.findings.shares.items()},
        "transit_within_1km_percent": round(result.findings.transit_near, 1),
        "packages": packages,
        "git": git,
        "results_file": str(RESULTS_PATH.relative_to(REPO_DIR)),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m pulse.cli", description="Run Penang Pulse and write its results.")
    parser.add_argument("--raw-dir", type=Path, default=ANALYSIS_DIR / "data/raw/pulse")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    files = {source: fetch(source, args.raw_dir) for source in FILE_SOURCES}
    osm = fetch_osm(args.raw_dir)
    inputs = Inputs(
        health=files[HEALTH].path,
        schools=files[SCHOOLS].path,
        gtfs=files[GTFS].path,
        dosm=files[DOSM].path,
        boundaries=files[BOUNDARIES].path,
        worldpop=str(files[WORLDPOP].path),
        meta=meta_path(files[META].path),
        osm=osm.path,
    )
    result = run(inputs)

    fetched = [*files.values(), osm]
    git = git_state()
    packages = {"python": platform.python_version(), **{name: version(name) for name in LIBRARIES}}
    manifest = build_manifest(fetched, result, packages, git)
    run_info = {"commit": git["commit"], "manifest": str(MANIFEST_PATH.relative_to(REPO_DIR)), "python": packages["python"], "lastRun": datetime.now(UTC).date().isoformat()}
    retrieved = {f.name: f.retrieved[:10] for f in fetched}
    results = build_results(result.findings, result.geometry, result.points, run_info, retrieved, files[GTFS].retrieved)
    write_json(MANIFEST_PATH, manifest)
    write_json(RESULTS_PATH, results)
    print(f"wrote {RESULTS_PATH.relative_to(REPO_DIR)} and {MANIFEST_PATH.relative_to(REPO_DIR)}")


if __name__ == "__main__":
    main()
