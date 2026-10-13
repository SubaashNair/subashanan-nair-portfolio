"""Mean absolute error with block bootstrap intervals over forecast origins."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

BLOCK_ORIGINS = 8  # two hours of consecutive origins per block, so nearby errors stay together
RESAMPLES = 2000
INTERVAL = (2.5, 97.5)


@dataclass(frozen=True)
class Estimate:
    point: float
    low: float
    high: float


def origin_errors(predicted: np.ndarray, actual: np.ndarray) -> np.ndarray:
    """Absolute error averaged over sensors, one value per origin. Both inputs are (origins, sensors)."""
    if predicted.shape != actual.shape:
        raise ValueError(f"shape mismatch {predicted.shape} and {actual.shape}")
    return np.abs(predicted - actual).mean(axis=1)


def block_resamples(origins: int, seed: int, block: int = BLOCK_ORIGINS, resamples: int = RESAMPLES) -> list[np.ndarray]:
    """Index sets for a non-overlapping block bootstrap: cut the origins into consecutive blocks, draw blocks with replacement."""
    blocks = [np.arange(start, min(start + block, origins)) for start in range(0, origins, block)]
    picks = np.random.default_rng(seed).integers(0, len(blocks), size=(resamples, len(blocks)))
    return [np.concatenate([blocks[j] for j in row]) for row in picks]


def mae(errors: np.ndarray, resamples: list[np.ndarray]) -> Estimate:
    draws = np.array([errors[idx].mean() for idx in resamples])
    low, high = np.percentile(draws, INTERVAL)
    return Estimate(point=float(errors.mean()), low=float(low), high=float(high))


def reduction(model: np.ndarray, baseline: np.ndarray, resamples: list[np.ndarray]) -> Estimate:
    """Percentage MAE reduction of `model` against `baseline`, paired: both use the same resampled origins."""
    draws = np.array([100 * (1 - model[idx].mean() / baseline[idx].mean()) for idx in resamples])
    low, high = np.percentile(draws, INTERVAL)
    return Estimate(point=float(100 * (1 - model.mean() / baseline.mean())), low=float(low), high=float(high))
