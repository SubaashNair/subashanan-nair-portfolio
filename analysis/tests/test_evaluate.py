import numpy as np
import pytest

from forecasting.evaluate import block_resamples, mae, origin_errors, reduction


def test_origin_errors_average_over_sensors() -> None:
    predicted = np.array([[1.0, 2.0], [3.0, 3.0]])
    actual = np.array([[2.0, 4.0], [3.0, 1.0]])
    assert origin_errors(predicted, actual).tolist() == [1.5, 1.0]


def test_origin_errors_reject_mismatched_shapes() -> None:
    with pytest.raises(ValueError):
        origin_errors(np.zeros((2, 3)), np.zeros((3, 2)))


def test_block_resamples_are_seeded_and_keep_blocks_whole() -> None:
    first = block_resamples(20, seed=42, block=8, resamples=50)
    second = block_resamples(20, seed=42, block=8, resamples=50)
    assert all((a == b).all() for a, b in zip(first, second, strict=True))
    for idx in first:
        starts = [i for i in idx if i % 8 == 0]
        assert len(starts) == 3  # three blocks per resample: 0 to 7, 8 to 15, 16 to 19


def test_mae_interval_brackets_the_point() -> None:
    errors = np.random.default_rng(0).uniform(0, 1, 100)
    estimate = mae(errors, block_resamples(100, seed=1))
    assert estimate.low <= estimate.point <= estimate.high
    assert estimate.point == pytest.approx(errors.mean())


def test_reduction_is_paired_and_signed() -> None:
    baseline = np.random.default_rng(0).uniform(1, 2, 64)
    resamples = block_resamples(64, seed=3)
    half = reduction(baseline / 2, baseline, resamples)
    assert half.point == pytest.approx(50) and half.low == pytest.approx(50) and half.high == pytest.approx(50)
    worse = reduction(baseline * 1.1, baseline, resamples)
    assert worse.point == pytest.approx(-10)
