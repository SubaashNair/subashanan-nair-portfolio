import numpy as np
import pytest

from forecasting.chronos_adapter import CONTEXT_LENGTH, chronos_forecasts
from forecasting.data import Traffic

from .fakes import FakeChronos


def test_context_ends_at_the_origin_and_respects_the_window(tiny: Traffic) -> None:
    fake = FakeChronos()
    chronos_forecasts(tiny.series, np.array([100, 900]), 8, fake)
    short, long = fake.contexts
    assert short.shape == (4, 101)
    np.testing.assert_array_equal(short[:, -1], tiny.series[:, 100])
    assert long.shape == (4, CONTEXT_LENGTH)
    np.testing.assert_array_equal(long[:, -1], tiny.series[:, 900])


def test_returns_the_median_sample_path(tiny: Traffic) -> None:
    out = chronos_forecasts(tiny.series, np.array([500]), 8, FakeChronos())
    assert out.shape == (1, 4, 8)
    np.testing.assert_allclose(out[0, :, 3], tiny.series[:, 500])


def test_rejects_a_predictor_with_the_wrong_shape(tiny: Traffic) -> None:
    def broken(context: np.ndarray, steps: int) -> np.ndarray:
        return np.zeros((context.shape[0], steps))

    with pytest.raises(ValueError, match="shape"):
        chronos_forecasts(tiny.series, np.array([500]), 8, broken)


def test_importing_the_adapter_does_not_import_torch() -> None:
    import sys

    assert "torch" not in sys.modules
