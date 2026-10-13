"""Chronos zero-shot forecasts. torch and chronos are imported only inside load_chronos, so tests never need them."""

from __future__ import annotations

from typing import Protocol

import numpy as np

CHRONOS_MODEL = "amazon/chronos-t5-small"
CHRONOS_REVISION = "a971ba21945c4f1796b17a91fe69214b5f4ad472"  # Hugging Face commit, read on 2026-10-13
CHRONOS_LICENCE = "Apache 2.0"
CONTEXT_LENGTH = 512  # chronos-t5 context window
NUM_SAMPLES = 20


class SamplePredictor(Protocol):
    def __call__(self, context: np.ndarray, steps: int) -> np.ndarray:
        """context (batch, length) to sample paths (batch, samples, steps)."""
        ...


def chronos_forecasts(series: np.ndarray, origins: np.ndarray, steps: int, predictor: SamplePredictor) -> np.ndarray:
    """(origins, sensors, steps): the median sample path, given each sensor's history up to and including the origin."""
    sensors = series.shape[0]
    rows: list[np.ndarray] = []
    for origin in origins:
        context = series[:, max(0, origin + 1 - CONTEXT_LENGTH) : origin + 1]
        samples = np.asarray(predictor(context, steps))
        if samples.ndim != 3 or samples.shape[0] != sensors or samples.shape[2] != steps:
            raise ValueError(f"predictor returned shape {samples.shape}, expected ({sensors}, samples, {steps})")
        rows.append(np.median(samples, axis=1))
    return np.stack(rows)


def load_chronos(seed: int) -> tuple[SamplePredictor, dict[str, str]]:
    """The real predictor on CPU, and the package versions to record. Needs `uv sync --group chronos`."""
    try:
        import chronos
        import torch
        from chronos import BaseChronosPipeline
    except ImportError as error:
        raise SystemExit("Chronos is not installed. Run: uv sync --group chronos") from error

    torch.manual_seed(seed)
    pipeline = BaseChronosPipeline.from_pretrained(CHRONOS_MODEL, revision=CHRONOS_REVISION, device_map="cpu", dtype=torch.float32)

    def predict(context: np.ndarray, steps: int) -> np.ndarray:
        with torch.no_grad():
            samples = pipeline.predict(torch.tensor(context, dtype=torch.float32), prediction_length=steps, num_samples=NUM_SAMPLES)
        return samples.numpy()

    return predict, {"torch": torch.__version__, "chronos-forecasting": chronos.__version__}
