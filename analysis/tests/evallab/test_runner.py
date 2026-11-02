import json
from pathlib import Path

import pytest

from evallab.ollama import OllamaError, UsageLimit
from evallab.questions import Question
from evallab.runner import BACKOFF_SECONDS, CAP_NOTE, MAX_TOOL_CALLS, Asker, RunLog, run
from evallab.store import Store

from .fake_ollama import FakeChat, final, tool_call

MODELS = ("gpt-oss:120b-cloud", "deepseek-v4.1-flash:cloud")


def lookup(model, messages, tools):
    """Search the releases, read the newest one's second page, then answer."""
    tool_replies = [m for m in messages if m["role"] == "tool"]
    if tools and not tool_replies:
        return {"role": "assistant", "content": "", "tool_calls": [tool_call("search_releases", query="unemployment rate")]}
    if tools and len(tool_replies) == 1:
        return {"role": "assistant", "content": "", "tool_calls": [tool_call("read_release", id="labour_month_2026-08", page=2)]}
    return final(2.9, "per cent", "2026-08", "https://open.dosm.gov.my/publications/labour_month_2026-08")


def asker(store: Store, tmp_path: Path, client: FakeChat, sleeps: list[float] | None = None) -> Asker:
    return Asker(client, store, RunLog(tmp_path), "2026-10-15", 1.5, (sleeps if sleeps is not None else []).append)


def test_with_tools_the_model_reads_the_snapshot_then_answers(store: Store, questions: list[Question], tmp_path: Path) -> None:
    client = FakeChat(lookup)
    outcome = asker(store, tmp_path, client).ask(MODELS[0], "tools", questions[0])

    assert (outcome.tool_calls, outcome.status) == (2, "ok") and '"value": 2.9' in outcome.content
    last = client.requests[-1]["messages"]
    assert [m["role"] for m in last] == ["system", "user", "assistant", "tool", "assistant", "tool"]
    assert "Today is 2026-10-15." in last[0]["content"] and last[1]["content"] == "What is Malaysia's latest unemployment rate?"
    assert "eased to 2.9 per cent" in json.loads(last[5]["content"])["text"]
    assert client.requests[0]["options"] == {"temperature": 0, "seed": 42} and client.requests[0]["tools"] is not None


def test_from_memory_there_are_no_tools_and_one_call(store: Store, questions: list[Question], tmp_path: Path) -> None:
    client = FakeChat(lookup)
    outcome = asker(store, tmp_path, client).ask(MODELS[0], "memory", questions[0])
    assert len(client.requests) == 1 and client.requests[0]["tools"] is None and outcome.tool_calls == 0


def test_parallel_tool_calls_count_one_by_one_and_the_cap_forces_an_answer(store: Store, questions: list[Question], tmp_path: Path) -> None:
    greedy = lambda model, messages, tools: (  # noqa: E731
        {"role": "assistant", "content": "", "tool_calls": [tool_call("search_datasets", query="unemployment")] * 4} if tools else final(3.0, "per cent", "2026-07", "lfs_month"))
    client = FakeChat(greedy)
    outcome = asker(store, tmp_path, client).ask(MODELS[1], "tools", questions[0])

    assert (outcome.tool_calls, outcome.status) == (MAX_TOOL_CALLS, "cap") and '"value": 3.0' in outcome.content
    assert [r["tools"] is not None for r in client.requests] == [True, True, False]
    refused = [m for m in client.requests[2]["messages"] if m["role"] == "tool"][-2:]
    assert all(json.loads(m["content"]) == {"error": CAP_NOTE} for m in refused)


def test_a_failing_call_is_retried_with_backoff_then_scored_as_no_answer(store: Store, questions: list[Question], tmp_path: Path) -> None:
    attempts = iter([OllamaError("timed out"), OllamaError("HTTP 502")])
    flaky = FakeChat(lambda m, msgs, t: next(attempts, final(2.9, "per cent", "2026-08", "lfs_month")))
    sleeps: list[float] = []
    assert asker(store, tmp_path, flaky, sleeps).ask(MODELS[0], "memory", questions[0]).status == "ok"
    assert sleeps == [BACKOFF_SECONDS, BACKOFF_SECONDS * 2, 1.5]

    broken = FakeChat(lambda m, msgs, t: OllamaError("HTTP 500"))
    outcome = asker(store, tmp_path / "broken", broken).ask(MODELS[0], "memory", questions[0])
    assert (outcome.content, outcome.status) == ("", "error") and len(broken.requests) == 3
    assert [c["status"] for c in RunLog(tmp_path / "broken").calls()] == ["error"] * 3


def test_a_usage_limit_stops_the_run_and_the_next_run_resumes(store: Store, questions: list[Question], tmp_path: Path) -> None:
    run_log, calls = RunLog(tmp_path), {"n": 0}

    def limited(model, messages, tools):
        calls["n"] += 1
        return UsageLimit("HTTP 429") if calls["n"] == 3 else final(1, "per cent", "2026-08", "x")

    with pytest.raises(UsageLimit):
        run(FakeChat(limited), store, questions[:2], MODELS, run_log, "2026-10-15", 0, sleep=lambda s: None)
    assert len(run_log.answers()) == 2 and run_log.calls()[-1]["status"] == "limit"

    resumed = FakeChat(lambda m, msgs, t: final(1, "per cent", "2026-08", "x"))
    assert run(resumed, store, questions[:2], MODELS, run_log, "2026-10-15", 0, sleep=lambda s: None) == 6
    keys = [(a["question"], a["model"], a["mode"]) for a in run_log.answers()]
    assert len(keys) == len(set(keys)) == 8


def test_a_line_cut_short_by_an_interruption_is_skipped(store: Store, questions: list[Question], tmp_path: Path) -> None:
    run_log = RunLog(tmp_path)
    run(FakeChat(lambda m, msgs, t: final(1, "per cent", "2026-08", "x")), store, questions[:1], MODELS[:1], run_log, "2026-10-15", 0, sleep=lambda s: None)
    with run_log.answers_path.open("a") as handle:
        handle.write('{"question": "q002", "mod')
    assert [a["question"] for a in run_log.answers()] == ["q001", "q001"]


def test_a_pilot_runs_only_the_chosen_questions(store: Store, questions: list[Question], tmp_path: Path) -> None:
    client = FakeChat(lambda m, msgs, t: final(1, "per cent", "2026-08", "x"))
    assert run(client, store, questions, MODELS, RunLog(tmp_path), "2026-10-15", 0, only={"q003"}, sleep=lambda s: None) == 4
    assert {r["messages"][1]["content"] for r in client.requests} == {questions[2].text}
