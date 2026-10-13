"""Turns a run into the site's ForecastResults JSON and a manifest. All prose comes from templates over computed numbers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .chronos_adapter import CHRONOS_MODEL
from .data import STEP_MINUTES, STEPS_PER_DAY, Block
from .evaluate import Estimate
from .models import HORIZON_STEPS, MAX_STEPS, MODEL_IDS, MODEL_NAMES
from .pipeline import Comparison, RunResult

EXPORT_SCALE = 100  # the publisher's 0 to 1 flow, shown as an index from 0 to 100
PAST_STEPS = 36
SENSOR_POSITIONS = (1 / 6, 1 / 2, 5 / 6)  # low, middle and high traffic sensors by mean test flow
SENTENCE_NAMES = {
    "persistence": "persistence",
    "seasonal": "the daily seasonal naive",
    "gb": "gradient boosting",
    "mlp": "the spatial MLP",
    "chronos": "Chronos",
}
LOCAL_CAVEAT = "One highway corridor near Washington DC, so treat the ranking as local."


def whole(value: float) -> str:
    return str(int(round(value)))


def oriented(estimate: Estimate) -> Estimate:
    """A reduction shown as a positive number, with its interval flipped to match when the change is an increase."""
    if estimate.point >= 0:
        return estimate
    return Estimate(point=-estimate.point, low=-estimate.high, high=-estimate.low)


def direction(estimate: Estimate) -> str:
    return "lower" if estimate.point >= 0 else "higher"


def interval(estimate: Estimate) -> str:
    shown = oriented(estimate)
    return f"95% interval {whole(shown.low)} to {whole(shown.high)}%"


def capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def answer_text(short: Comparison, long: Comparison) -> str:
    first = (
        f"At {short.minutes} minutes, {SENTENCE_NAMES[short.model]}, the tuned model chosen on validation data, has "
        f"{whole(oriented(short.estimate).point)}% {direction(short.estimate)} error than persistence ({interval(short.estimate)})."
    )
    second = (
        f"At {long.minutes // 60} hours, Chronos, used with no tuning, has {whole(oriented(long.estimate).point)}% "
        f"{direction(long.estimate)} error than {SENTENCE_NAMES[long.against]}, the better tuned model on validation data ({interval(long.estimate)})."
    )
    return f"{first} {second}"


def key_numbers(short: Comparison, long: Comparison, sensors: int, test_hours: int) -> list[dict[str, str]]:
    bootstrap = "from a block bootstrap over the test window."
    return [
        {
            "value": f"{whole(oriented(short.estimate).point)}%",
            "label": f"{direction(short.estimate)} error than persistence for {SENTENCE_NAMES[short.model]} at {short.minutes} minutes.",
            "caveat": f"{capital(interval(short.estimate))}, {bootstrap}",
        },
        {
            "value": f"{whole(oriented(long.estimate).point)}%",
            "label": f"{direction(long.estimate)} error for Chronos, with no tuning, than {SENTENCE_NAMES[long.against]} at {long.minutes // 60} hours.",
            "caveat": f"{capital(interval(long.estimate))}, {bootstrap}",
        },
        {
            "value": str(sensors),
            "label": f"sensors scored at {len(HORIZON_STEPS)} horizons on the final {test_hours} hours of data.",
            "caveat": LOCAL_CAVEAT,
        },
    ]


def pick_sensors(series: np.ndarray, test: Block) -> list[int]:
    order = np.argsort(series[:, test.start : test.stop].mean(axis=1), kind="stable")
    return [int(order[int(q * (len(order) - 1))]) for q in SENSOR_POSITIONS]


def pick_origin(series: np.ndarray, sensor: int, origins: np.ndarray) -> int:
    """Index into origins of the window where this sensor's flow changes most over the forecast horizon."""
    usable = origins >= PAST_STEPS
    change = np.abs(series[sensor, origins + MAX_STEPS] - series[sensor, origins])
    return int(np.argmax(np.where(usable, change, -np.inf)))


def scaled(values: np.ndarray) -> list[float]:
    return [round(float(v) * EXPORT_SCALE, 2) for v in values]


def sensor_entry(result: RunResult, series: np.ndarray, sensor: int) -> dict[str, Any]:
    k = pick_origin(series, sensor, result.origins)
    origin = int(result.origins[k])
    start = series[sensor, origin]
    forecasts = {m: scaled(np.concatenate([[start], result.forecasts[m][k, sensor, :]])) for m in MODEL_IDS}
    window = {m: float(np.abs(result.forecasts[m][k, sensor, :] - result.actual[k, sensor, :]).mean()) for m in MODEL_IDS}
    return {
        "id": f"s{sensor + 1}",
        "label": f"Sensor {sensor + 1}",
        "originMinutes": (origin % STEPS_PER_DAY) * STEP_MINUTES,
        "stepMinutes": STEP_MINUTES,
        "pastSteps": PAST_STEPS,
        "actual": scaled(series[sensor, origin - PAST_STEPS : origin + MAX_STEPS + 1]),
        "forecasts": forecasts,
        "windowMae": {m: round(v * EXPORT_SCALE, 2) for m, v in window.items()},
    }


def build_results(result: RunResult, series: np.ndarray, test: Block, run: dict[str, str], retrieved: dict[str, str]) -> dict[str, Any]:
    test_hours = (test.stop - test.start) * STEP_MINUTES // 60
    return {
        "answer": answer_text(result.short, result.long),
        "keyNumbers": key_numbers(result.short, result.long, series.shape[0], test_hours),
        "run": run,
        "retrieved": retrieved,
        "horizons": [s * STEP_MINUTES for s in HORIZON_STEPS],
        "models": [{"id": m, "name": MODEL_NAMES[m], "mae": [round(e.point * EXPORT_SCALE, 2) for e in result.mae[m]]} for m in MODEL_IDS],
        "sensors": [sensor_entry(result, series, i) for i in pick_sensors(series, test)],
    }


def estimate_json(estimate: Estimate, scale: float = 1) -> dict[str, float]:
    return {"point": round(estimate.point * scale, 4), "low": round(estimate.low * scale, 4), "high": round(estimate.high * scale, 4)}


def comparison_json(comparison: Comparison) -> dict[str, Any]:
    return {"model": comparison.model, "against": comparison.against, "minutes": comparison.minutes, "reduction_percent": estimate_json(comparison.estimate)}


def scores_json(result: RunResult) -> dict[str, Any]:
    return {
        "test_origins": [int(result.origins[0]), int(result.origins[-1])],
        "mae_index_points": {
            m: [{"minutes": s * STEP_MINUTES, **estimate_json(e, EXPORT_SCALE)} for s, e in zip(HORIZON_STEPS, result.mae[m], strict=True)]
            for m in MODEL_IDS
        },
        "short": comparison_json(result.short),
        "long": comparison_json(result.long),
        "chronos_model": CHRONOS_MODEL,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
