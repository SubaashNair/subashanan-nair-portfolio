import numpy as np
import pytest

from forecasting.data import Traffic, make_split
from forecasting.models import HORIZON_STEPS, MAX_STEPS, MODEL_IDS, eval_origins
from forecasting.pipeline import RunResult


def test_every_model_forecasts_every_test_origin(tiny: Traffic, tiny_run: RunResult) -> None:
    origins = eval_origins(make_split(tiny.series.shape[1]).test)
    np.testing.assert_array_equal(tiny_run.origins, origins)
    for model in MODEL_IDS:
        assert tiny_run.forecasts[model].shape == (origins.size, 4, MAX_STEPS)
        assert len(tiny_run.mae[model]) == len(HORIZON_STEPS)


def test_actual_values_are_the_test_targets(tiny: Traffic, tiny_run: RunResult) -> None:
    first = int(tiny_run.origins[0])
    np.testing.assert_array_equal(tiny_run.actual[0, :, 0], tiny.series[:, first + 1])
    assert first + 1 == make_split(tiny.series.shape[1]).test.start


def test_comparisons_name_the_right_models(tiny_run: RunResult) -> None:
    assert tiny_run.short.against == "persistence" and tiny_run.short.minutes == 15
    assert tiny_run.short.model != "persistence"
    assert tiny_run.long.model == "chronos" and tiny_run.long.against in ("gb", "mlp") and tiny_run.long.minutes == 120


def test_persistence_error_matches_a_hand_computation(tiny: Traffic, tiny_run: RunResult) -> None:
    o = tiny_run.origins
    expected = np.abs(tiny.series[:, o + 1] - tiny.series[:, o]).mean()
    assert tiny_run.mae["persistence"][0].point == pytest.approx(expected)
