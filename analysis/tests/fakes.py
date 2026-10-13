"""Test doubles: a Chronos stand-in that needs no torch, and small model grids that train in seconds."""

import numpy as np

from forecasting.models import Settings

QUICK = Settings(
    gb_grid=({"learning_rate": 0.1, "max_leaf_nodes": 7}, {"learning_rate": 0.2, "max_leaf_nodes": 7}),
    mlp_grid=({"hidden_layer_sizes": [8], "alpha": 1e-3},),
    gb_iterations=20,
    mlp_iterations=30,
)


class FakeChronos:
    """Sample paths centred on the latest reading."""

    def __init__(self, samples: int = 5) -> None:
        self.samples = samples
        self.contexts: list[np.ndarray] = []

    def __call__(self, context: np.ndarray, steps: int) -> np.ndarray:
        self.contexts.append(context)
        latest = context[:, -1][:, None, None]
        spread = np.linspace(-0.01, 0.01, self.samples)[None, :, None]
        return np.broadcast_to(latest + spread, (context.shape[0], self.samples, steps)).copy()
