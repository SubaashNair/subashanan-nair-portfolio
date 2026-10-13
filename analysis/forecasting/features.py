"""Features built from the flow series itself. A row for origin t only reads values at t or earlier."""

from __future__ import annotations

import numpy as np

from .data import STEPS_PER_DAY, WEEKDAYS

LAGS = 10
NEIGHBOUR_WINDOW = 4
FIRST_ORIGIN = max(LAGS, NEIGHBOUR_WINDOW) - 1


def feature_names() -> list[str]:
    lags = [f"lag_{k}" for k in range(LAGS)]
    calendar = ["slot_sin", "slot_cos", *[f"weekday_{d}" for d in range(WEEKDAYS)]]
    return [*lags, "neighbour_now", f"neighbour_mean_{NEIGHBOUR_WINDOW}", *calendar]


def neighbour_means(series: np.ndarray, adjacency: np.ndarray) -> np.ndarray:
    """Mean flow of each sensor's neighbours at every step. Column t uses column t only."""
    weights = adjacency / adjacency.sum(axis=1, keepdims=True)
    return weights @ series


def calendar_features(origins: np.ndarray) -> np.ndarray:
    angle = 2 * np.pi * (origins % STEPS_PER_DAY) / STEPS_PER_DAY
    weekday = np.eye(WEEKDAYS)[(origins // STEPS_PER_DAY) % WEEKDAYS]
    return np.column_stack([np.sin(angle), np.cos(angle), weekday])


def build_features(series: np.ndarray, adjacency: np.ndarray, origins: np.ndarray) -> np.ndarray:
    """One row per (origin, sensor), origin-major, so row k * sensors + i is sensor i at origins[k]."""
    origins = np.asarray(origins, dtype=np.int64)
    if origins.size == 0 or origins.min() < FIRST_ORIGIN or origins.max() >= series.shape[1]:
        raise ValueError(f"origins must lie in [{FIRST_ORIGIN}, {series.shape[1]})")
    sensors = series.shape[0]
    neighbours = neighbour_means(series, adjacency)
    lags = np.stack([series[:, origins - k] for k in range(LAGS)], axis=-1)
    recent = np.stack([neighbours[:, origins - k] for k in range(NEIGHBOUR_WINDOW)], axis=-1).mean(axis=-1)
    calendar = np.broadcast_to(calendar_features(origins), (sensors, origins.size, 2 + WEEKDAYS))
    per_sensor = np.concatenate([lags, neighbours[:, origins, None], recent[..., None], calendar], axis=-1)
    return per_sensor.transpose(1, 0, 2).reshape(origins.size * sensors, -1)


def targets(series: np.ndarray, origins: np.ndarray, steps: int) -> np.ndarray:
    """Flow `steps` ahead of each origin, in the same row order as build_features."""
    return series[:, np.asarray(origins) + steps].T.reshape(-1)
