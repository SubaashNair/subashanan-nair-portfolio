import json

import pytest

from evallab.questions import Question
from evallab.scoring import as_period, bootstrap, cites, in_unit, parse_answer, score_answer, score_runs, views
from evallab.statistics import STATISTICS

BY_ID = {s.id: s for s in STATISTICS}
KNOWN = frozenset({"lfs_month_youth", "domains", "https://open.dosm.gov.my/publications/labour_month_2026-08"})


@pytest.mark.parametrize(("content", "expected"), [
    ('Here it is:\n```json\n{"value": 10.1, "unit": "per cent", "period": "2026-08", "source": "x"}\n```', 10.1),
    ('The rate was 10.1%. {"value": "10.1", "period": "August 2026"} Hope that helps.', "10.1"),
    ('{"value": 9, "period": "2026-01"} then I checked again: {"value": 10.1, "period": "2026-08"}', 10.1),
    ('{"value": 10.1, "unit": "per cent"}', None),  # no period
    ("I could not find it.", None),
    ('{"value": 10.1, "period": "2026-08"', None),  # cut short
])
def test_parse_answer_takes_the_last_complete_json_answer(content: str, expected: object) -> None:
    answer = parse_answer(content)
    assert (answer or {}).get("value") == expected


@pytest.mark.parametrize(("statistic", "value", "unit", "expected"), [
    ("m3", 2.64, "RM trillion", 2640.0),
    ("m3", "RM2.64 trillion", "", 2640.0),
    ("m3", "2,636,548.8", "RM million", 2636.5488),
    ("employed_persons", 16874.4, "thousand persons", 16.8744),
    ("youth_rate_15_24", "10.1%", "per cent", 10.1),
    ("domains_active", "693,122", "domains", 693122.0),
    ("youth_rate_15_24", True, "per cent", None),
    ("youth_rate_15_24", "not published", "per cent", None),
])
def test_values_are_converted_to_the_statistics_unit(statistic: str, value: object, unit: str, expected: float | None) -> None:
    assert in_unit(value, unit, BY_ID[statistic]) == (pytest.approx(expected) if expected is not None else None)


@pytest.mark.parametrize(("text", "quarterly", "expected"), [
    ("2026-08", False, "2026-08"), ("2026-08-01", False, "2026-08"), ("August 2026", False, "2026-08"), ("Aug. 2026", False, "2026-08"),
    ("Ogos 2026", False, "2026-08"), ("08/2026", False, "2026-08"), ("2026-Q2", True, "2026-Q2"), ("Q2 2026", True, "2026-Q2"),
    ("2Q 2026", True, "2026-Q2"), ("second quarter of 2026", True, "2026-Q2"), ("suku kedua 2026", True, "2026-Q2"), ("ST2 2026", True, "2026-Q2"),
    ("June 2026", True, "2026-Q2"), ("2026-Q2", False, None), ("2026", False, None), ("latest", False, None), (None, False, None), ("2026-13", False, None),
])
def test_periods_are_read_in_english_and_malay(text: object, quarterly: bool, expected: str | None) -> None:
    assert as_period(text, quarterly) == expected


def test_a_source_must_name_something_in_the_snapshot() -> None:
    assert cites("lfs_month_youth", KNOWN) and cites("data.gov.my dataset lfs_month_youth.", KNOWN)
    assert cites("DOSM, https://open.dosm.gov.my/publications/labour_month_2026-08", KNOWN)
    assert not cites("lfs_month_youth_2", KNOWN) and not cites("domains_ipv6", KNOWN) and not cites("https://www.dosm.gov.my", KNOWN) and not cites(None, KNOWN)


def question(value: float, period: str, status: str = "out of date", statistic: str = "youth_rate_15_24", id: str = "q001", language: str = "en") -> Question:
    return Question(id, statistic, language, "?", value, "per cent", period, "", 10.2, "2026-06", status)


def answer(value: object, period: str, source: str = "lfs_month_youth", unit: str = "per cent") -> str:
    return json.dumps({"value": value, "unit": unit, "period": period, "source": source})


def test_scores_check_value_at_the_publications_rounding_and_period() -> None:
    youth = BY_ID["youth_rate_15_24"]
    right = score_answer(answer(10.14, "Aug 2026"), question(10.1, "2026-08"), youth, KNOWN)
    assert right.latest and right.source_ok
    stale = score_answer(answer(10.2, "June 2026"), question(10.1, "2026-08"), youth, KNOWN)
    assert (stale.value_ok, stale.period_ok, stale.latest, stale.value, stale.period) == (False, False, False, 10.2, "2026-06")
    half = score_answer(answer(4.95, "2026-08"), question(5.0, "2026-08"), youth, KNOWN)  # rounds half up, as publications do
    assert half.value_ok
    unreadable = score_answer("No idea.", question(10.1, "2026-08"), youth, KNOWN)
    assert not unreadable.readable and not unreadable.latest


def test_the_bootstrap_resamples_statistics_not_questions() -> None:
    # Two statistics with four questions each: one always right, one always wrong. Resampling whole statistics gives
    # shares of only 0, 50 or 100, so the interval spans 0 to 100; resampling single questions would be far narrower.
    results = [("a", True)] * 4 + [("b", False)] * 4
    assert bootstrap(results) == (0.0, 100.0)
    assert bootstrap(results, seed=7) == bootstrap(results, seed=7)


def test_views_need_every_answer_and_keep_the_baseline_out_of_memory() -> None:
    questions = [question(10.1, "2026-08", id="q001"), question(2.9, "2026-08", status="current", statistic="unemployment_rate", id="q002", language="ms")]
    records = [{"question": q.id, "model": m, "mode": mode, "content": answer(q.value if m == "a" else 1.0, q.period), "tool_calls": 2, "seconds": 3.0}
               for q in questions for m, mode in (("a", "tools"), ("a", "memory"), ("baseline", "tools"))]
    records.append({**records[0], "content": "a duplicate is ignored"})
    runs = score_runs(records, questions, BY_ID, KNOWN)
    cells = views(runs, questions, ("a",))
    assert {v: [(c.model, c.share, c.questions) for c in cs] for v, cs in cells.items()} == {
        "all-tools": [("a", 100.0, 2), ("baseline", 0.0, 2)],
        "stale-tools": [("a", 100.0, 1), ("baseline", 0.0, 1)],
        "all-memory": [("a", 100.0, 2)],
    }
    assert cells["all-tools"][0].by_language == {"en": 100.0, "ms": 100.0} and cells["all-tools"][0].calls == 2.0
    assert cells["all-tools"][0].sourced == 100.0
    with pytest.raises(ValueError, match="a has no memory answer for 1 questions, such as q002"):
        views([r for r in runs if not (r.mode == "memory" and r.question.id == "q002")], questions, ("a",))
