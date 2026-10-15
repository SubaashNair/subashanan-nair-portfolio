import pytest

from tools.update_cv import FORECAST_TECH_NEW, FORECAST_TECH_OLD, PULSE_BULLET, PULSE_TECH_NEW, bullet_lines, change, choose, forecast_text, pulse_text, wrap

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


PULSE = {
    "keyNumbers": [
        {"value": "21%", "label": "of Seberang Perai Selatan residents live more than 3 km by road from a public clinic."},
        {"value": "2,437", "label": "public clinics, schools and Rapid Penang stops mapped."},
        {"value": "58%", "label": "of Penang residents live within 1 km by road of a Rapid Penang stop."},
    ]
}


def test_pulse_text_uses_only_numbers_from_the_results() -> None:
    preferred, spec, short = pulse_text(PULSE)
    assert preferred == (
        "Road distance from every populated 100 m cell in Penang to the nearest of 2,437 public clinics, schools and bus stops. "
        "21% of Seberang Perai Selatan residents live over 3 km from a clinic; 58% of all residents live within 1 km of a bus stop."
    )
    assert spec == (
        "Road distance from every populated 100 m cell in Penang to the nearest public clinic, school and bus stop; "
        "21% of Seberang Perai Selatan residents live over 3 km from a clinic."
    )
    assert short.startswith("Road distance from every populated cell")
    assert all(text.startswith(PULSE_BULLET[-1]) for text in (preferred, spec, short))  # so a later run finds the bullet again


def test_pulse_text_capitalises_a_share_under_1_percent_that_starts_a_sentence() -> None:
    low = {"keyNumbers": [{**PULSE["keyNumbers"][0], "value": "under 1%"}, *PULSE["keyNumbers"][1:]]}
    assert " stops. Under 1% of Seberang Perai Selatan" in pulse_text(low)[0]
    assert "; under 1% of Seberang Perai Selatan" in pulse_text(low)[1]


def test_pulse_tech_line_names_what_the_pipeline_uses() -> None:
    assert "Pydantic" not in PULSE_TECH_NEW and "Penang GeoHub" not in PULSE_TECH_NEW
    assert all(name in PULSE_TECH_NEW for name in ("NetworkX", "rasterio", "Shapely", "pyosmium", "OpenStreetMap", "WorldPop", "DOSM data"))


def raw_line(x: float, baseline: float, text: str, font: str = "Helvetica", size: float = 9.5) -> dict:
    chars = [{"c": c, "bbox": (x + 5 * i, baseline - 9, x + 5 * i + 5, baseline + 3)} for i, c in enumerate(text)]
    return {"bbox": (x, baseline - 10, x + 5 * len(text), baseline + 3), "spans": [{"size": size, "font": font, "origin": (x, baseline), "chars": chars}]}


class FakePage:
    def __init__(self, *lines: dict) -> None:
        self.lines = lines

    def get_text(self, kind: str) -> dict:
        return {"blocks": [{"lines": [line]} for line in reversed(self.lines)]}  # out of order, as inserted text is


def test_bullet_lines_finds_text_an_earlier_run_inserted_beside_its_bullet() -> None:
    page = FakePage(
        raw_line(54.8, 169.7, "•  ", font="LiberationSans"),
        raw_line(63.4, 169.7, "In progress: a reproducible study of how far"),
        raw_line(64.9, 181.1, "and transit stop, using PeGIS"),
        raw_line(64.9, 192.5, "limitations are published ahead of any results."),
        raw_line(50.5, 207.3, "Forecasting Lab", font="LiberationSans-Bold", size=10.0),
    )
    assert [(line.x, line.baseline) for line in bullet_lines(page, PULSE_BULLET)] == [(63.4, 169.7), (64.9, 181.1), (64.9, 192.5)]


def test_bullet_lines_finds_the_original_bullet_and_stops_at_the_next_one() -> None:
    page = FakePage(
        raw_line(54.8, 169.7, "•  Reproducible study of how evenly clinics", font="LiberationSans"),
        raw_line(64.9, 181.1, "schools and transit stops", font="LiberationSans"),
        raw_line(54.8, 192.5, "•  Another bullet", font="LiberationSans"),
    )
    assert [(line.x, line.baseline) for line in bullet_lines(page, PULSE_BULLET)] == [(54.8 + 15, 169.7), (64.9, 181.1)]
    with pytest.raises(SystemExit, match="No line starts with"):
        bullet_lines(page, ("Leakage safe",))
