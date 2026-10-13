import pytest

from tools.update_cv import FORECAST_TECH_NEW, FORECAST_TECH_OLD, change, choose, forecast_text, wrap

RESULTS = {
    "horizons": [15, 30, 60, 90, 120],
    "keyNumbers": [{}, {}, {"value": "36"}],
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
    full, short = forecast_text(RESULTS)
    assert full == (
        "Leakage safe 15 minute traffic forecasting benchmark across a 36 sensor network. At 15 minutes versus persistence, "
        "MAE fell 25% with gradient boosting, fell 5% with a spatial MLP and rose 5% with zero-shot Chronos."
    )
    assert short.endswith("At 15 minutes, MAE fell 25% with gradient boosting versus persistence.")


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
