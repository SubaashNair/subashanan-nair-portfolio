from pathlib import Path

import pytest

from evallab import cli
from evallab.cli import MODELS, pilot_ids, pilot_summary, usage
from evallab.questions import Question
from evallab.runner import RunLog
from evallab.store import Store


def test_the_pilot_spreads_twenty_questions_over_the_set(questions: list[Question]) -> None:
    hundred_twenty = [Question(f"q{i:03d}", "s", "en", "", 0, "", "", "", 0, "", "") for i in range(1, 121)]
    chosen = sorted(pilot_ids(hundred_twenty))
    assert len(chosen) == 20 and chosen[:3] == ["q001", "q007", "q013"]
    assert pilot_ids(questions) == {q.id for q in questions}  # fewer than 20: all of them


def test_usage_counts_calls_errors_and_tokens() -> None:
    calls = [{"model": "m", "mode": "tools", "status": "ok", "prompt_tokens": 10, "output_tokens": 2},
             {"model": "m", "mode": "tools", "status": "error"}, {"model": "m", "mode": "memory", "status": "limit"}]
    assert usage(calls) == {"m": {"tools": {"calls": 2, "errors": 1, "prompt_tokens": 10, "output_tokens": 2},
                                  "memory": {"calls": 1, "errors": 1, "prompt_tokens": 0, "output_tokens": 0}}}


def test_the_pilot_summary_shows_usage_timing_and_outcomes(answered: RunLog) -> None:
    summary = pilot_summary(answered.answers(), answered.calls())
    tools = summary[MODELS[0]]["tools"]
    assert {k: v for k, v in tools.items() if k != "median_seconds"} == {
        "calls": 32, "errors": 0, "prompt_tokens": 3200, "output_tokens": 640, "answers": 16, "tool_calls": 16, "statuses": {"ok": 16}}
    assert tools["median_seconds"] >= 0
    assert summary[MODELS[1]]["memory"]["calls"] == 16


def test_the_run_refuses_to_start_when_ollama_is_not_reachable(store: Store, questions: list[Question], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sheet = tmp_path / "questions.csv"
    monkeypatch.setattr(cli, "read_questions", lambda path, statistics: questions)
    real = cli.OllamaClient
    monkeypatch.setattr(cli, "OllamaClient", lambda: real("http://127.0.0.1:9", timeout=2))  # nothing listens on port 9
    with pytest.raises(SystemExit, match="Ollama is not reachable at the start of the run"):
        cli.main(["--raw-dir", str(store.root), "--questions", str(sheet), "run"])
