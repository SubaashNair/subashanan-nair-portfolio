"""Test doubles: small model grids that train in seconds."""

from forecasting.models import Settings

QUICK = Settings(
    gb_grid=({"learning_rate": 0.1, "max_leaf_nodes": 7}, {"learning_rate": 0.2, "max_leaf_nodes": 7}),
    mlp_grid=({"hidden_layer_sizes": [8], "alpha": 1e-3},),
    gb_iterations=20,
    mlp_iterations=30,
)
