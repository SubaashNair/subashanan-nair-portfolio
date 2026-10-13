import pytest

from tools.update_cv import FORECAST_TECH_NEW, FORECAST_TECH_OLD, change, choose, forecast_text, wrap

RESULTS = {
    "horizons": [15, 30, 60, 90, 120],
    "keyNumbers": [
        {
            "value": "23%",
            "label": "lower error than persistence for gradient boosting at 15 minutes.",
            "caveat": "95% interval 16 to 30%, from a block bootstrap over the test window.",
        },
        {
            "value": "26%",
            "label": "lower error for Chronos, with no tuning, than gradient boosting at 2 hours.",
            "caveat": "95% interval 17 to 34%, from a block bootstrap over the test window.",
        },
        {"value": "36"},
    ],
    "models": [
        {"id": "persistence", "mae": [2.0]},
        {"id": "seasonal", "mae": [4.0]},
        {"id": "gb", "mae": [1.5]},
        {"id": "mlp", "mae": [1.9]},
        {"id": "chronos", "mae": [2.1]},
    ],
}


def chars(text: str) -> float:
    return float(len(text))


def test_change_names_the_direction() -> None:
    assert change("gradient boosting", 24.6) == "fell 25% with gradient boosting"
    assert change("zero-shot Chronos", -5.2) == "rose 5% with zero-shot Chronos"


def test_forecast_text_uses_only_numbers_from_the_results() -> None:
    preferred, full, short = forecast_text(RESULTS)
    assert preferred == (
        "Leakage safe 15 minute traffic forecasting benchmark across a 36 sensor network. "
        "Gradient boosting cut MAE 23% (95% interval 16 to 30%) versus persistence at 15 minutes; "
        "zero-shot Chronos beat it by 26% at 2 hours."
    )
    assert full == (
        "Leakage safe 15 minute traffic forecasting benchmark across a 36 sensor network. At 15 minutes versus persistence, "
        "MAE fell 25% with gradient boosting, fell 5% with a spatial MLP and rose 5% with zero-shot Chronos."
    )
    assert short.endswith("At 15 minutes, MAE fell 25% with gradient boosting versus persistence.")


def test_the_two_hour_rival_is_named_when_it_differs() -> None:
    mlp = {**RESULTS, "keyNumbers": [RESULTS["keyNumbers"][0], {**RESULTS["keyNumbers"][1], "label": "lower error for Chronos, with no tuning, than the spatial MLP at 2 hours."}, RESULTS["keyNumbers"][2]]}
    assert forecast_text(mlp)[0].endswith("zero-shot Chronos beat the spatial MLP by 26% at 2 hours.")


def test_the_interval_wording_is_skipped_unless_both_changes_are_reductions() -> None:
    worse = {**RESULTS, "keyNumbers": [RESULTS["keyNumbers"][0], {**RESULTS["keyNumbers"][1], "label": "higher error for Chronos, with no tuning, than gradient boosting at 2 hours."}, RESULTS["keyNumbers"][2]]}
    assert len(forecast_text(worse)) == 2


def test_wrap_respects_each_line_width_and_the_line_count() -> None:
    assert wrap("aa bb cc dd", chars, [5, 5]) == ["aa bb", "cc dd"]
    assert wrap("aa bb cc dd", chars, [5]) is None


def test_choose_falls_back_to_a_shorter_wording_then_fails() -> None:
    assert choose(("aa bb cc dd ee", "aa bb"), chars, [5, 5]) == ["aa bb"]
    with pytest.raises(SystemExit, match="shorten"):
        choose(("aaaaaa",), chars, [5])


def test_forecast_tech_line_swaps_pydantic_for_what_the_pipeline_uses() -> None:
    assert "Pydantic" in FORECAST_TECH_OLD
    assert FORECAST_TECH_NEW == FORECAST_TECH_OLD.replace("Pydantic", "PyTorch, Chronos")
