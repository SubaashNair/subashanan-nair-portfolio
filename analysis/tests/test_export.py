import re

import numpy as np

from forecasting.data import Traffic, make_split
from forecasting.evaluate import Estimate
from forecasting.export import EXPORT_SCALE, PAST_STEPS, answer_text, build_results, key_numbers, lead_sentence, pick_sensors
from forecasting.models import MAX_STEPS, MODEL_IDS
from forecasting.pipeline import Comparison, RunResult

RUN = {"commit": "abc1234", "manifest": "analysis/outputs/forecasting-lab-manifest.json", "python": "3.12.9", "lastRun": "2026-10-13"}
RETRIEVED = {"Dataset 608": "2026-10-13", "chronos-t5-small": "2026-10-13"}
DASHES = re.compile("[–—]")  # en and em dashes


def results(tiny: Traffic, run: RunResult) -> dict:
    return build_results(run, tiny.series, make_split(tiny.series.shape[1]).test, RUN, RETRIEVED)


def test_matches_the_site_chart_contract(tiny: Traffic, tiny_run: RunResult) -> None:
    out = results(tiny, tiny_run)
    assert out["horizons"] == [15, 30, 60, 90, 120]
    assert [m["id"] for m in out["models"]] == list(MODEL_IDS)
    assert all(len(m["mae"]) == 5 for m in out["models"])
    assert len(out["sensors"]) == 3
    for sensor in out["sensors"]:
        assert sensor["pastSteps"] == PAST_STEPS and sensor["stepMinutes"] == 15
        assert len(sensor["actual"]) == PAST_STEPS + MAX_STEPS + 1
        assert 0 <= sensor["originMinutes"] < 24 * 60
        for model in MODEL_IDS:
            assert len(sensor["forecasts"][model]) == MAX_STEPS + 1
            assert sensor["forecasts"][model][0] == sensor["actual"][PAST_STEPS]
            assert sensor["windowMae"][model] >= 0


def test_numbers_are_scaled_computed_values(tiny: Traffic, tiny_run: RunResult) -> None:
    out = results(tiny, tiny_run)
    persistence = next(m for m in out["models"] if m["id"] == "persistence")
    assert persistence["mae"][0] == round(tiny_run.mae["persistence"][0].point * EXPORT_SCALE, 2)
    assert out["keyNumbers"][2]["value"] == "4"


def test_three_key_numbers_with_the_required_fields(tiny: Traffic, tiny_run: RunResult) -> None:
    numbers = results(tiny, tiny_run)["keyNumbers"]
    assert len(numbers) == 3
    for n in numbers:
        assert set(n) == {"value", "label", "caveat"} and all(n.values())


def test_prose_follows_the_copy_rules(tiny: Traffic, tiny_run: RunResult) -> None:
    out = results(tiny, tiny_run)
    prose = [out["answer"], *[f'{n["label"]} {n["caveat"]}' for n in out["keyNumbers"]]]
    for text in prose:
        assert not DASHES.search(text) and "→" not in text  # no arrows


def test_templates_say_lower_or_higher_from_the_sign() -> None:
    better = Comparison("gb", "persistence", 15, Estimate(point=21.6, low=15.2, high=27.9))
    worse = Comparison("chronos", "mlp", 120, Estimate(point=-8.4, low=-14.0, high=-2.5))
    assert answer_text(better, worse) == (
        "At 15 minutes, gradient boosting, the tuned model chosen on validation data, has 22% lower error than persistence (95% interval 15 to 28%). "
        "At 2 hours, Chronos, used with no tuning, has 8% higher error than the spatial MLP, the better tuned model on validation data (95% interval 2 to 14%)."
    )
    numbers = key_numbers(better, worse, 36, 51)
    assert numbers[0] == {
        "value": "22%",
        "label": "lower error than persistence for gradient boosting at 15 minutes.",
        "caveat": "95% interval 15 to 28%, from a block bootstrap over the test window.",
    }
    assert numbers[1]["label"] == "higher error for Chronos, with no tuning, than the spatial MLP at 2 hours."
    assert numbers[2]["label"] == "sensors scored at 5 horizons on the final 51 hours of data."


def test_picks_three_distinct_sensors_from_low_to_high_flow(tiny: Traffic) -> None:
    picked = pick_sensors(tiny.series, make_split(tiny.series.shape[1]).test)
    assert picked == [0, 1, 2]
    wide = np.tile(np.arange(36.0)[:, None], (1, 1300)) / 36
    assert pick_sensors(wide, make_split(1300).test) == [5, 17, 29]


def table(first: dict[str, float], rest: float = 1.0) -> dict[str, list[Estimate]]:
    """Fabricated MAEs: the first horizon from `first`, then Chronos lowest at the other four unless `rest` is high."""
    out = {}
    for model, value in first.items():
        later = 0.5 if model == "chronos" else rest
        out[model] = [Estimate(point=v, low=v, high=v) for v in (value, later, later, later, later)]
    return out


def test_lead_sentence_calls_a_narrow_first_horizon_lead_small() -> None:
    mae = table({"persistence": 2.0, "gb": 1.02, "mlp": 1.5, "chronos": 1.0})  # 2% lead over gradient boosting
    assert lead_sentence(mae) == (
        "Chronos also had the lowest error at every horizon, although its lead over gradient boosting at 15 minutes is small and was not tested."
    )


def test_lead_sentence_drops_the_small_claim_for_a_clear_lead() -> None:
    mae = table({"persistence": 2.0, "gb": 1.5, "mlp": 1.6, "chronos": 1.0})  # 33% lead
    assert lead_sentence(mae) == "Chronos also had the lowest error at every horizon."


def test_lead_sentence_is_empty_unless_chronos_wins_every_horizon() -> None:
    mae = table({"persistence": 2.0, "gb": 1.02, "mlp": 1.5, "chronos": 1.0})
    mae["gb"][3] = Estimate(point=0.1, low=0.1, high=0.1)
    assert lead_sentence(mae) == ""
    assert not DASHES.search(lead_sentence(table({"persistence": 2.0, "gb": 1.02, "chronos": 1.0})))


def test_the_local_caveat_names_both_highways(tiny: Traffic, tiny_run: RunResult) -> None:
    assert results(tiny, tiny_run)["keyNumbers"][2]["caveat"] == "Two highways near Washington DC, so treat the ranking as local."
