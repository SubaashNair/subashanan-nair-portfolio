import json
import re

import pytest

from evallab.export import answer_text, error_examples, figure, key_numbers, long_date, period_label, row
from evallab.questions import Question
from evallab.scoring import Cell, score_runs
from evallab.statistics import STATISTICS

BY_ID = {s.id: s for s in STATISTICS}
DASHES = re.compile("[–—←-↓]")
GPT, DEEPSEEK = "gpt-oss:120b-cloud", "deepseek-v4.1-flash:cloud"


def cell(model: str, share: float, low: float = 10.0, high: float = 90.0) -> Cell:
    return Cell(model, share, low, high, 3.25, 8.04, 40, {"en": share, "ms": share})


def views(gpt: float, deepseek: float, memory: float = 20.0) -> dict[str, list[Cell]]:
    return {
        "all-tools": [cell(GPT, 70.0), cell(DEEPSEEK, 60.0), cell("baseline", 50.0)],
        "stale-tools": [cell(GPT, gpt, 41.2, 79.6), cell(DEEPSEEK, deepseek), cell("baseline", 0.0, 0.0, 0.0)],
        "all-memory": [cell(GPT, memory), cell(DEEPSEEK, 15.0)],
    }


def test_the_answer_names_the_leader_on_out_of_date_series() -> None:
    assert answer_text(views(62.4, 48.0)) == (
        "On out-of-date series, gpt-oss 120B gave the latest official figure for 62% of questions with tools, against 0% for the open data alone.")


def test_a_tie_on_rounded_shares_names_both_models() -> None:
    text = answer_text(views(62.4, 61.6))
    assert text.startswith("On out-of-date series, gpt-oss 120B and DeepSeek V4.1 Flash tied, each giving the latest official figure for 62%")
    first = key_numbers(views(62.4, 61.6), 30, 120, "2026-10-16")[0]
    assert first["label"].endswith("by gpt-oss 120B and DeepSeek V4.1 Flash, with tools.") and first["caveat"].endswith("Interval for gpt-oss 120B.")


def test_key_numbers_come_from_the_views() -> None:
    first, change, size = key_numbers(views(62.4, 48.0), 30, 120, "2026-10-16")
    assert first == {"value": "62%", "label": "of questions on out-of-date series answered with the latest figure by gpt-oss 120B, with tools.",
                     "caveat": "95% interval 41 to 80%, from a bootstrap over statistics."}
    assert change == {"value": "50 points", "label": "higher latest-figure share for gpt-oss 120B with tools than from memory, across all series.",
                      "caveat": "From 20% from memory to 70% with tools."}
    assert size == {"value": "30", "label": "statistics, asked 4 ways each: 120 questions verified against the official release.",
                    "caveat": "Snapshot of open data and releases taken on 16 October 2026; results describe that day."}


@pytest.mark.parametrize(("memory", "value", "start"), [(69.0, "1 point", "higher"), (71.0, "1 point", "lower"), (70.0, "0 points", "difference for gpt-oss 120B")])
def test_the_change_from_memory_reads_well_at_any_size(memory: float, value: str, start: str) -> None:
    change = key_numbers(views(62.4, 48.0, memory), 30, 120, "2026-10-16")[1]
    assert change["value"] == value and change["label"].startswith(start)


def test_rows_round_half_up_and_keep_the_score_inside_its_interval() -> None:
    assert row(Cell(GPT, 62.5, 62.6, 80.0, 3.25, 8.04, 40, {})) == {
        "model": "gpt-oss 120B", "role": "cloud", "score": 63, "low": 63, "high": 80, "callsPerAnswer": 3.25, "callsLabel": "3.2", "latency": "8.0 s"}
    baseline = row(Cell("baseline", 50.0, 38.0, 66.0, 0.0, 0.00002, 120, {}))
    assert (baseline["model"], baseline["role"], baseline["callsLabel"], baseline["latency"]) == ("Open data only", "baseline", "0", "under 0.1 s")


def test_labels_for_periods_figures_and_dates() -> None:
    assert (period_label("2026-08"), period_label("2026-Q2"), long_date("2026-10-16")) == ("August 2026", "Q2 2026", "16 October 2026")
    assert figure(2636.5488, BY_ID["m3"]) == "RM2,636.5 billion" and figure(46.5, BY_ID["productivity_hour"]) == "RM46.5 per hour"
    assert figure(693122.0, BY_ID["domains_active"]) == "693,122 domains" and figure(10.1, BY_ID["youth_rate_15_24"]) == "10.1 per cent"


def youth(id: str, text: str = "What is it?") -> Question:
    return Question(id, "youth_rate_15_24", "en", text, 10.1, "per cent", "2026-08", "", 10.2, "2026-06", "out of date")


def reply(value: object, period: str) -> str:
    return json.dumps({"value": value, "unit": "per cent", "period": period, "source": "lfs_month_youth"})


def test_error_examples_follow_the_rules_in_order() -> None:
    questions = [youth(f"q00{i}") for i in range(1, 9)]
    contents = [reply(10.2, "2026-06"), reply(10.2, "2026-06"), reply(10.2, "2026-06"), reply(10.1, "2026-07"), "Sorry.", "", reply(10.1, "2026-08"), reply(9.0, "2026-08")]
    records = [{"question": q.id, "model": GPT, "mode": "tools", "content": c, "tool_calls": 1, "seconds": 1.0} for q, c in zip(questions, contents, strict=True)]
    records += [{"question": "q001", "model": DEEPSEEK, "mode": "memory", "content": "", "tool_calls": 0, "seconds": 1.0},
                {"question": "q001", "model": "baseline", "mode": "tools", "content": reply(10.2, "2026-06"), "tool_calls": 0, "seconds": 0.0}]
    examples = error_examples(score_runs(records, questions, BY_ID, frozenset()), BY_ID)

    assert [(e["input"], e["note"]) for e in examples] == [
        ("What is it?", "Gave the open dataset's figure for June 2026, not the release for August 2026."),
        ("What is it?", "Gave the open dataset's figure for June 2026, not the release for August 2026."),
        ("What is it?", "Named July 2026 instead of August 2026."),
        ("What is it?", "No final JSON answer could be read."),
        ("What is it?", "No final JSON answer could be read."),
    ]
    assert examples[0] == {"input": "What is it?", "expected": "10.1 per cent, August 2026", "model": "gpt-oss 120B, with tools",
                           "output": "10.2 per cent, June 2026", "note": examples[0]["note"], "correct": False}
    assert examples[3]["output"] == "No final answer"
    for line in [answer_text(views(62.4, 61.6)), *[v for k in key_numbers(views(62.4, 61.6), 30, 120, "2026-10-16") for v in k.values()], *[e["note"] for e in examples]]:
        assert not DASHES.search(line)