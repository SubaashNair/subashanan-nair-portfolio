"""Download, verify and load UCI dataset 608, and define the chronological split."""

from __future__ import annotations

import hashlib
import json
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import scipy.io

SOURCE_NAME = "Dataset 608"
SOURCE_TITLE = "UCI Machine Learning Repository dataset 608, Traffic Flow Forecasting"
SOURCE_URL = "https://archive.ics.uci.edu/static/public/608/traffic+flow+forecasting.zip"
SOURCE_PAGE = "https://archive.ics.uci.edu/dataset/608/traffic+flow+forecasting"
SOURCE_DOI = "10.24432/C57897"
SOURCE_LICENCE = "CC BY 4.0"  # read from SOURCE_PAGE on 2026-10-13; re-checked in Task 11
MAT_NAME = "traffic_dataset.mat"
ZIP_NAME = "traffic_flow_forecasting.zip"
RETRIEVED_NAME = "retrieved.json"

STEP_MINUTES = 15
STEPS_PER_DAY = 96
WEEKDAYS = 5  # the publisher's calendar has weekdays only
TRAIN_DAYS = 9
VAL_DAYS = 2
WEEKDAY_COLUMNS = slice(10, 15)  # publisher feature layout inside each 36x48 matrix
HOUR_COLUMNS = slice(15, 39)


@dataclass(frozen=True)
class Traffic:
    series: np.ndarray  # (sensors, steps), the publisher's flow scaled to 0 to 1
    adjacency: np.ndarray  # (sensors, sensors), 0 or 1, symmetric, zero diagonal


@dataclass(frozen=True)
class Block:
    start: int
    stop: int  # exclusive

    def as_list(self) -> list[int]:
        return [self.start, self.stop]


@dataclass(frozen=True)
class Split:
    train: Block
    val: Block
    test: Block


@dataclass(frozen=True)
class RawFiles:
    zip_path: Path
    mat_path: Path
    retrieved: str  # ISO 8601 timestamp, UTC


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(raw_dir: Path) -> RawFiles:
    """Download the zip once, record when, and extract the .mat file. Later runs reuse the cache."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / ZIP_NAME
    stamp_path = raw_dir / RETRIEVED_NAME
    if not zip_path.exists() or not stamp_path.exists():
        urllib.request.urlretrieve(SOURCE_URL, zip_path)
        stamp = datetime.now(UTC).replace(microsecond=0).isoformat()
        stamp_path.write_text(json.dumps({"retrieved": stamp}))
    with zipfile.ZipFile(zip_path) as archive:
        archive.extract(MAT_NAME, raw_dir)
    retrieved = json.loads(stamp_path.read_text())["retrieved"]
    return RawFiles(zip_path=zip_path, mat_path=raw_dir / MAT_NAME, retrieved=retrieved)


def _dense(cell: object) -> np.ndarray:
    return cell.toarray() if hasattr(cell, "toarray") else np.asarray(cell)


def check_calendar(features: np.ndarray, steps: int) -> None:
    """Fail unless the publisher's weekday and hour fields match our step-based calendar."""
    for t in range(steps):
        row = _dense(features[0, t])[0]
        weekday = int(np.argmax(row[WEEKDAY_COLUMNS]))
        hour = int(np.argmax(row[HOUR_COLUMNS]))
        if (weekday, hour) != (weekday_of(t), hour_of(t)):
            raise ValueError(f"step {t}: publisher calendar says weekday {weekday} hour {hour}")


def load(mat_path: Path) -> Traffic:
    raw = scipy.io.loadmat(mat_path)
    series = np.asarray(raw["tra_Y_tr"], dtype=np.float64)
    adjacency = np.asarray(raw["tra_adj_mat"], dtype=np.int64)
    sensors, steps = series.shape
    if adjacency.shape != (sensors, sensors):
        raise ValueError(f"adjacency is {adjacency.shape}, expected {(sensors, sensors)}")
    if not np.isfinite(series).all():
        raise ValueError("series has missing or infinite values")
    if not (adjacency == adjacency.T).all() or adjacency.diagonal().any():
        raise ValueError("adjacency must be symmetric with a zero diagonal")
    if (adjacency.sum(axis=1) == 0).any():
        raise ValueError("every sensor needs at least one neighbour")
    check_calendar(raw["tra_X_tr"], steps)
    return Traffic(series=series, adjacency=adjacency)


def weekday_of(step: int) -> int:
    return (step // STEPS_PER_DAY) % WEEKDAYS


def hour_of(step: int) -> int:
    return (step % STEPS_PER_DAY) * STEP_MINUTES // 60


def make_split(steps: int) -> Split:
    train_stop = TRAIN_DAYS * STEPS_PER_DAY
    val_stop = train_stop + VAL_DAYS * STEPS_PER_DAY
    if steps <= val_stop:
        raise ValueError(f"need more than {val_stop} steps, got {steps}")
    return Split(train=Block(0, train_stop), val=Block(train_stop, val_stop), test=Block(val_stop, steps))
