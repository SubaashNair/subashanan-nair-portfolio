"""Runs every model on the test origins and scores them. No file or network access here."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .chronos_adapter import SamplePredictor, chronos_forecasts
from .data import STEP_MINUTES, Split, Traffic
from .evaluate import Estimate, block_resamples, mae, origin_errors, reduction
from .models import HORIZON_STEPS, MAX_STEPS, MODEL_IDS, Settings, eval_origins, persistence, seasonal, tuned_forecasts

TUNED = ("gb", "mlp")


@dataclass(frozen=True)
class Comparison:
    model: str
    against: str
    minutes: int
    estimate: Estimate


@dataclass(frozen=True)
class RunResult:
    origins: np.ndarray  # test origins
    actual: np.ndarray  # (origins, sensors, MAX_STEPS)
    forecasts: dict[str, np.ndarray]  # model id to (origins, sensors, MAX_STEPS)
    mae: dict[str, list[Estimate]]  # model id to one estimate per horizon in HORIZON_STEPS
    short: Comparison  # the better tuned model, chosen on validation MAE, against persistence at the first horizon
    long: Comparison  # Chronos against the better tuned model at the last horizon
    tuning: dict[str, dict[int, dict[str, Any]]]


def actual_ahead(series: np.ndarray, origins: np.ndarray) -> np.ndarray:
    return np.stack([series[:, origins + s].T for s in range(1, MAX_STEPS + 1)], axis=2)


def run(traffic: Traffic, split: Split, predictor: SamplePredictor, settings: Settings, seed: int) -> RunResult:
    series, adjacency = traffic.series, traffic.adjacency
    origins = eval_origins(split.test)
    gb, gb_tuning = tuned_forecasts("gb", series, adjacency, split, origins, settings, seed)
    mlp, mlp_tuning = tuned_forecasts("mlp", series, adjacency, split, origins, settings, seed)
    tuning = {"gb": gb_tuning, "mlp": mlp_tuning}
    forecasts = {
        "persistence": persistence(series, origins),
        "seasonal": seasonal(series, origins),
        "gb": gb,
        "mlp": mlp,
        "chronos": chronos_forecasts(series, origins, MAX_STEPS, predictor),
    }
    actual = actual_ahead(series, origins)
    resamples = block_resamples(origins.size, seed)
    errors = {m: {s: origin_errors(forecasts[m][:, :, s - 1], actual[:, :, s - 1]) for s in HORIZON_STEPS} for m in MODEL_IDS}
    scores = {m: [mae(errors[m][s], resamples) for s in HORIZON_STEPS] for m in MODEL_IDS}
    return RunResult(
        origins=origins,
        actual=actual,
        forecasts=forecasts,
        mae=scores,
        short=compare_short(errors, tuning, resamples),
        long=compare_long(errors, tuning, resamples),
        tuning=tuning,
    )


def compare_short(errors: dict[str, dict[int, np.ndarray]], tuning: dict[str, dict[int, dict[str, Any]]], resamples: list[np.ndarray]) -> Comparison:
    first = HORIZON_STEPS[0]
    best = min(TUNED, key=lambda m: tuning[m][first]["val_mae"])
    estimate = reduction(errors[best][first], errors["persistence"][first], resamples)
    return Comparison(model=best, against="persistence", minutes=first * STEP_MINUTES, estimate=estimate)


def compare_long(errors: dict[str, dict[int, np.ndarray]], tuning: dict[str, dict[int, dict[str, Any]]], resamples: list[np.ndarray]) -> Comparison:
    last = HORIZON_STEPS[-1]
    tuned = min(TUNED, key=lambda m: tuning[m][last]["val_mae"])
    estimate = reduction(errors["chronos"][last], errors[tuned][last], resamples)
    return Comparison(model="chronos", against=tuned, minutes=last * STEP_MINUTES, estimate=estimate)
