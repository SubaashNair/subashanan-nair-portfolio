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
    assert tiny_run.short.model in ("gb", "mlp")
    assert tiny_run.long.model == "chronos" and tiny_run.long.against in ("gb", "mlp") and tiny_run.long.minutes == 120


def test_persistence_error_matches_a_hand_computation(tiny: Traffic, tiny_run: RunResult) -> None:
    o = tiny_run.origins
    expected = np.abs(tiny.series[:, o + 1] - tiny.series[:, o]).mean()
    assert tiny_run.mae["persistence"][0].point == pytest.approx(expected)


def test_comparisons_pick_by_validation_not_test_mae() -> None:
    """When validation and test MAE disagree, pick the validation winner."""
    from forecasting.models import HORIZON_STEPS
    from forecasting.pipeline import compare_short, compare_long

    # Fabricate errors where "gb" has better test MAE but "mlp" has better val MAE
    first = HORIZON_STEPS[0]
    last = HORIZON_STEPS[-1]
    origins = 16

    # Test errors: gb better at first, mlp better at last
    errors = {
        "gb": {first: np.array([0.1] * origins), last: np.array([0.3] * origins)},
        "mlp": {first: np.array([0.2] * origins), last: np.array([0.2] * origins)},
        "persistence": {first: np.array([0.3] * origins), last: np.array([0.5] * origins)},
        "chronos": {first: np.array([0.15] * origins), last: np.array([0.25] * origins)},
        "seasonal": {first: np.array([0.25] * origins), last: np.array([0.35] * origins)},
    }

    # Validation errors: opposite - mlp better at first, gb better at last
    tuning = {
        "gb": {first: {"val_mae": 0.25}, last: {"val_mae": 0.1}},
        "mlp": {first: {"val_mae": 0.15}, last: {"val_mae": 0.3}},
    }

    # Resamples with all indices (one bootstrap replicate using all data)
    resamples = [np.arange(origins)]

    # compare_short should pick "mlp" because it has better val_mae at first horizon
    short = compare_short(errors, tuning, resamples)
    assert short.model == "mlp", "should pick model with best validation MAE"

    # compare_long should pick "gb" because it has better val_mae at last horizon
    long = compare_long(errors, tuning, resamples)
    assert long.against == "gb", "should pick baseline with best validation MAE"
