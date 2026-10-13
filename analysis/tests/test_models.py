import numpy as np
import pytest

from forecasting.data import Traffic, make_split
from forecasting.features import build_features
from forecasting.models import (
    MAX_STEPS,
    eval_origins,
    persistence,
    scaler_of,
    seasonal,
    train_origins,
    tune,
    tuned_forecasts,
)

from .fakes import QUICK


def test_persistence_repeats_the_latest_reading(tiny: Traffic) -> None:
    out = persistence(tiny.series, np.array([300, 301]))
    assert out.shape == (2, 4, MAX_STEPS)
    assert (out[1, 2, :] == tiny.series[2, 301]).all()


def test_seasonal_reads_one_publisher_day_back(tiny: Traffic) -> None:
    out = seasonal(tiny.series, np.array([300]))
    assert out[0, 3, 0] == tiny.series[3, 301 - 96]
    assert out[0, 3, MAX_STEPS - 1] == tiny.series[3, 300 + MAX_STEPS - 96]


def test_seasonal_refuses_origins_without_a_day_of_history(tiny: Traffic) -> None:
    with pytest.raises(ValueError):
        seasonal(tiny.series, np.array([10]))


def test_training_targets_stay_inside_the_training_block() -> None:
    split = make_split(1100)
    for steps in range(1, MAX_STEPS + 1):
        assert train_origins(split, steps).max() + steps < split.train.stop


def test_evaluation_targets_stay_inside_their_block() -> None:
    split = make_split(1100)
    origins = eval_origins(split.test)
    assert origins.min() + 1 == split.test.start
    assert origins.max() + MAX_STEPS == split.test.stop - 1


def test_mlp_scaler_statistics_come_from_training_rows_only(tiny: Traffic) -> None:
    split = make_split(tiny.series.shape[1])
    tuned = tune("mlp", tiny.series, tiny.adjacency, split, 2, QUICK, seed=42)
    train_x = build_features(tiny.series, tiny.adjacency, train_origins(split, 2))
    np.testing.assert_allclose(scaler_of(tuned.estimator).mean_, train_x.mean(axis=0))
    with_val = build_features(tiny.series, tiny.adjacency, np.arange(9, split.val.stop - 2))
    assert not np.allclose(scaler_of(tuned.estimator).mean_, with_val.mean(axis=0))


def test_tuning_picks_the_lowest_validation_error(tiny: Traffic) -> None:
    tuned = tune("gb", tiny.series, tiny.adjacency, make_split(tiny.series.shape[1]), 1, QUICK, seed=42)
    assert tuned.val_mae == min(c["val_mae"] for c in tuned.candidates)
    assert len(tuned.candidates) == 2


def test_tuned_forecasts_are_reproducible_with_a_seed(tiny: Traffic) -> None:
    split = make_split(tiny.series.shape[1])
    origins = eval_origins(split.test)[:5]
    first, chosen = tuned_forecasts("gb", tiny.series, tiny.adjacency, split, origins, QUICK, seed=7)
    second, _ = tuned_forecasts("gb", tiny.series, tiny.adjacency, split, origins, QUICK, seed=7)
    assert first.shape == (5, 4, MAX_STEPS)
    np.testing.assert_array_equal(first, second)
    assert sorted(chosen) == list(range(1, MAX_STEPS + 1))
