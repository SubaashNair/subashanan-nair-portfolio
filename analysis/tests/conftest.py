"""A tiny synthetic stand-in for traffic_dataset.mat: 4 sensors, 1100 steps, the publisher's calendar fields."""

from pathlib import Path

import numpy as np
import pytest
import scipy.io

from forecasting.data import HOUR_COLUMNS, STEPS_PER_DAY, WEEKDAY_COLUMNS, Traffic, hour_of, load, weekday_of

SENSORS = 4
STEPS = 1100
ADJACENCY = np.array([[0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0]], dtype=np.uint8)


def synthetic_series(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(STEPS)
    daily = 0.35 + 0.25 * np.sin(2 * np.pi * (t % STEPS_PER_DAY) / STEPS_PER_DAY - 1.2)
    levels = np.array([0.6, 0.9, 1.0, 1.2])[:, None]
    return np.clip(levels * daily + rng.normal(0, 0.02, (SENSORS, STEPS)), 0, 1)


def calendar_cells(steps: int, sensors: int = SENSORS) -> np.ndarray:
    cells = np.empty((1, steps), dtype=object)
    for t in range(steps):
        cell = np.zeros((sensors, 48))
        cell[:, WEEKDAY_COLUMNS.start + weekday_of(t)] = 1
        cell[:, HOUR_COLUMNS.start + hour_of(t)] = 1
        cells[0, t] = cell
    return cells


def write_mat(path: Path, series: np.ndarray, adjacency: np.ndarray = ADJACENCY, cells: np.ndarray | None = None) -> Path:
    cells = calendar_cells(series.shape[1], series.shape[0]) if cells is None else cells
    scipy.io.savemat(path, {"tra_Y_tr": series, "tra_X_tr": cells, "tra_adj_mat": adjacency})
    return path


@pytest.fixture(scope="session")
def tiny_mat(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return write_mat(tmp_path_factory.mktemp("raw") / "traffic_dataset.mat", synthetic_series())


@pytest.fixture(scope="session")
def tiny(tiny_mat: Path) -> Traffic:
    return load(tiny_mat)
