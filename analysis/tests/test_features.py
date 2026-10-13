import numpy as np
import pytest

from forecasting.data import Traffic
from forecasting.features import FIRST_ORIGIN, LAGS, build_features, feature_names, neighbour_means, targets


def test_one_row_per_origin_and_sensor_with_named_columns(tiny: Traffic) -> None:
    origins = np.array([100, 101, 102])
    x = build_features(tiny.series, tiny.adjacency, origins)
    assert x.shape == (3 * 4, len(feature_names()))
    assert len(feature_names()) == 19


def test_lags_read_the_origin_and_earlier(tiny: Traffic) -> None:
    x = build_features(tiny.series, tiny.adjacency, np.array([500]))
    names = feature_names()
    for sensor in range(4):
        assert x[sensor, names.index("lag_0")] == tiny.series[sensor, 500]
        assert x[sensor, names.index(f"lag_{LAGS - 1}")] == tiny.series[sensor, 500 - LAGS + 1]


def test_neighbour_mean_averages_adjacent_sensors(tiny: Traffic) -> None:
    means = neighbour_means(tiny.series, tiny.adjacency)
    assert np.isclose(means[1, 300], (tiny.series[0, 300] + tiny.series[2, 300]) / 2)
    assert np.isclose(means[0, 300], tiny.series[1, 300])


def test_no_feature_uses_values_after_its_origin(tiny: Traffic) -> None:
    origins = np.arange(FIRST_ORIGIN, 700)
    future_changed = tiny.series.copy()
    future_changed[:, 700:] = 99.0
    before = build_features(tiny.series, tiny.adjacency, origins)
    after = build_features(future_changed, tiny.adjacency, origins)
    np.testing.assert_array_equal(before, after)


def test_rejects_origins_without_enough_history(tiny: Traffic) -> None:
    with pytest.raises(ValueError):
        build_features(tiny.series, tiny.adjacency, np.array([FIRST_ORIGIN - 1]))


def test_targets_follow_the_feature_row_order(tiny: Traffic) -> None:
    y = targets(tiny.series, np.array([200, 201]), 4)
    assert y.tolist() == [*tiny.series[:, 204].tolist(), *tiny.series[:, 205].tolist()]
