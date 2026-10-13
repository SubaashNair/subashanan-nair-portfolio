"""Entry point: python -m forecasting.cli --seed 42 (run from analysis/ after `uv sync --group chronos`)."""

from __future__ import annotations

import argparse
import logging
import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from . import data
from .chronos_adapter import CHRONOS_LICENCE, CHRONOS_MODEL, CHRONOS_REVISION, CONTEXT_LENGTH, NUM_SAMPLES, load_chronos
from .evaluate import BLOCK_ORIGINS, INTERVAL, RESAMPLES
from .export import EXPORT_SCALE, build_results, scores_json, write_json
from .features import feature_names
from .models import FULL, HORIZON_STEPS, MAX_STEPS
from .pipeline import RunResult, run

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ANALYSIS_DIR.parent
RESULTS_PATH = REPO_DIR / "apps/web/src/content/results/forecasting-lab.json"
MANIFEST_PATH = ANALYSIS_DIR / "outputs/forecasting-lab-manifest.json"


def git_state() -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=REPO_DIR, capture_output=True, text=True, check=True).stdout.strip()

    return {"commit": git("rev-parse", "--short", "HEAD"), "dirty": bool(git("status", "--porcelain"))}


def build_manifest(
    raw: data.RawFiles, split: data.Split, result: RunResult, seed: int, packages: dict[str, str], git: dict[str, Any]
) -> dict[str, Any]:
    return {
        "study": "forecasting-lab",
        "source": {
            "title": data.SOURCE_TITLE,
            "url": data.SOURCE_URL,
            "page": data.SOURCE_PAGE,
            "doi": data.SOURCE_DOI,
            "licence": data.SOURCE_LICENCE,
            "retrieved": raw.retrieved,
            "zip_sha256": data.sha256_of(raw.zip_path),
            "mat_sha256": data.sha256_of(raw.mat_path),
        },
        "calendar": {
            "step_minutes": data.STEP_MINUTES,
            "steps_per_day": data.STEPS_PER_DAY,
            "weekdays_only": True,
            "note": "Clock times follow the publisher's hour and weekday fields in tra_X_tr, checked at load time.",
        },
        "split": {"train": split.train.as_list(), "val": split.val.as_list(), "test": split.test.as_list()},
        "features": feature_names(),
        "horizon_steps": list(HORIZON_STEPS),
        "forecast_steps": MAX_STEPS,
        "seeds": {"models": seed, "bootstrap": seed, "torch": seed},
        "bootstrap": {
            "method": "non-overlapping block bootstrap over test origins",
            "block_origins": BLOCK_ORIGINS,
            "resamples": RESAMPLES,
            "percentiles": list(INTERVAL),
        },
        "tuning": {kind: {str(steps): chosen for steps, chosen in per_step.items()} for kind, per_step in result.tuning.items()},
        "chronos": {
            "model": CHRONOS_MODEL,
            "revision": CHRONOS_REVISION,
            "licence": CHRONOS_LICENCE,
            "context_length": CONTEXT_LENGTH,
            "num_samples": NUM_SAMPLES,
            "point_forecast": "median of samples",
        },
        "scores": scores_json(result),
        "export_scale": EXPORT_SCALE,
        "packages": packages,
        "git": git,
        "results_file": str(RESULTS_PATH.relative_to(REPO_DIR)),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m forecasting.cli", description="Run the Forecasting Lab and write its results.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--raw-dir", type=Path, default=ANALYSIS_DIR / "data/raw")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    raw = data.fetch(args.raw_dir)
    traffic = data.load(raw.mat_path)
    split = data.make_split(traffic.series.shape[1])
    predictor, chronos_versions = load_chronos(args.seed)
    result = run(traffic, split, predictor, FULL, args.seed)

    today = datetime.now(UTC).date().isoformat()
    git = git_state()
    libraries = {name: version(name) for name in ("numpy", "scipy", "scikit-learn")}
    packages = {"python": platform.python_version(), **libraries, **chronos_versions}
    write_json(MANIFEST_PATH, build_manifest(raw, split, result, args.seed, packages, git))
    manifest_name = str(MANIFEST_PATH.relative_to(REPO_DIR))
    run_info = {"commit": git["commit"], "manifest": manifest_name, "python": packages["python"], "lastRun": today}
    retrieved = {data.SOURCE_NAME: raw.retrieved[:10], "chronos-t5-small": today}
    write_json(RESULTS_PATH, build_results(result, traffic.series, split.test, run_info, retrieved))
    print(f"wrote {RESULTS_PATH.relative_to(REPO_DIR)} and {MANIFEST_PATH.relative_to(REPO_DIR)}")


if __name__ == "__main__":
    main()
