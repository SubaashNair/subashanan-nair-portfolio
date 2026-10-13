"""Baselines and the two tuned scikit-learn models. Every model forecasts steps 1 to MAX_STEPS directly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import STEPS_PER_DAY, Block, Split
from .features import FIRST_ORIGIN, build_features, targets

MAX_STEPS = 8
HORIZON_STEPS = (1, 2, 4, 6, 8)
MODEL_IDS = ("persistence", "seasonal", "gb", "mlp", "chronos")
MODEL_NAMES = {
    "persistence": "Persistence",
    "seasonal": "Daily seasonal naive",
    "gb": "Gradient boosting",
    "mlp": "Spatial MLP",
    "chronos": "Chronos, zero-shot",
}


@dataclass(frozen=True)
class Settings:
    gb_grid: tuple[dict[str, Any], ...]
    mlp_grid: tuple[dict[str, Any], ...]
    gb_iterations: int
    mlp_iterations: int


FULL = Settings(
    gb_grid=tuple({"learning_rate": lr, "max_leaf_nodes": leaves} for lr in (0.05, 0.1) for leaves in (15, 31)),
    mlp_grid=tuple({"hidden_layer_sizes": size, "alpha": alpha} for size in ((64,), (128, 64)) for alpha in (1e-4, 1e-3)),
    gb_iterations=300,
    mlp_iterations=200,
)


@dataclass(frozen=True)
class Tuned:
    estimator: Any
    params: dict[str, Any]
    val_mae: float
    candidates: list[dict[str, Any]]


def persistence(series: np.ndarray, origins: np.ndarray) -> np.ndarray:
    """(origins, sensors, MAX_STEPS): the latest reading, repeated."""
    latest = series[:, origins].T
    return np.repeat(latest[:, :, None], MAX_STEPS, axis=2)


def seasonal(series: np.ndarray, origins: np.ndarray) -> np.ndarray:
    """(origins, sensors, MAX_STEPS): the reading one publisher day (96 steps) before each target."""
    lookup = origins[:, None] + np.arange(1, MAX_STEPS + 1)[None, :] - STEPS_PER_DAY
    if lookup.min() < 0:
        raise ValueError("seasonal naive needs a full day of history before the first origin")
    return series[:, lookup].transpose(1, 0, 2)


def train_origins(split: Split, steps: int) -> np.ndarray:
    """Origins whose target `steps` ahead still falls inside the training block."""
    return np.arange(FIRST_ORIGIN, split.train.stop - steps)


def eval_origins(block: Block) -> np.ndarray:
    """Origins whose targets at every step from 1 to MAX_STEPS fall inside the block."""
    origins = np.arange(block.start - 1, block.stop - MAX_STEPS)
    if origins.size == 0:
        raise ValueError(f"block {block} is too short to score {MAX_STEPS} steps ahead")
    return origins


def make_estimator(kind: str, params: dict[str, Any], settings: Settings, seed: int) -> Any:
    if kind == "gb":
        return HistGradientBoostingRegressor(max_iter=settings.gb_iterations, early_stopping=False, random_state=seed, **params)
    if kind == "mlp":
        mlp = MLPRegressor(max_iter=settings.mlp_iterations, early_stopping=False, random_state=seed, **params)
        return make_pipeline(StandardScaler(), mlp)
    raise ValueError(f"unknown model kind {kind}")


def tune(kind: str, series: np.ndarray, adjacency: np.ndarray, split: Split, steps: int, settings: Settings, seed: int) -> Tuned:
    """Fit each grid point on train, score it on validation, keep the best. Validation is never used for fitting."""
    grid = settings.gb_grid if kind == "gb" else settings.mlp_grid
    fit_origins = train_origins(split, steps)
    x_train, y_train = build_features(series, adjacency, fit_origins), targets(series, fit_origins, steps)
    val = eval_origins(split.val)
    x_val, y_val = build_features(series, adjacency, val), targets(series, val, steps)
    fitted = [make_estimator(kind, params, settings, seed).fit(x_train, y_train) for params in grid]
    scores = [float(np.mean(np.abs(estimator.predict(x_val) - y_val))) for estimator in fitted]
    best = int(np.argmin(scores))  # the first minimum wins a tie
    candidates = [{**_jsonable(params), "val_mae": score} for params, score in zip(grid, scores, strict=True)]
    return Tuned(estimator=fitted[best], params=_jsonable(grid[best]), val_mae=scores[best], candidates=candidates)


def tuned_forecasts(
    kind: str, series: np.ndarray, adjacency: np.ndarray, split: Split, origins: np.ndarray, settings: Settings, seed: int
) -> tuple[np.ndarray, dict[int, dict[str, Any]]]:
    """(origins, sensors, MAX_STEPS) predictions from one tuned model per step, plus the chosen settings per step."""
    sensors = series.shape[0]
    x = build_features(series, adjacency, origins)
    columns: list[np.ndarray] = []
    chosen: dict[int, dict[str, Any]] = {}
    for steps in range(1, MAX_STEPS + 1):
        tuned = tune(kind, series, adjacency, split, steps, settings, seed)
        columns.append(tuned.estimator.predict(x).reshape(origins.size, sensors))
        chosen[steps] = {"params": tuned.params, "val_mae": tuned.val_mae, "candidates": tuned.candidates}
    return np.stack(columns, axis=2), chosen


def scaler_of(estimator: Pipeline) -> StandardScaler:
    return estimator.named_steps["standardscaler"]


def _jsonable(params: dict[str, Any]) -> dict[str, Any]:
    return {k: list(v) if isinstance(v, tuple) else v for k, v in params.items()}
