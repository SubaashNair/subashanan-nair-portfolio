from pathlib import Path
from typing import Any

import pytest

from evallab.cli import MODELS
from evallab.questions import Question, draft_all, read_questions, sheet_rows, write_sheet
from evallab.runner import RunLog, run
from evallab.store import Store, load

from .fake_ollama import FakeChat, Script, final, tool_call
from .world import STATS, take_snapshot


@pytest.fixture(scope="session")
def store(tmp_path_factory: pytest.TempPathFactory) -> Store:
    """The synthetic snapshot, taken once and shared by every test that only reads it."""
    root: Path = tmp_path_factory.mktemp("snapshot")
    take_snapshot(root)
    return load(root)


@pytest.fixture(scope="session")
def questions(store: Store, tmp_path_factory: pytest.TempPathFactory) -> list[Question]:
    """The synthetic world's 16 questions, drafted and marked verified as Subashanan would."""
    path = tmp_path_factory.mktemp("questions") / "questions.csv"
    write_sheet(path, [{**row, "verified": "yes"} for row in sheet_rows(draft_all(store, STATS))])
    return read_questions(path, STATS)


def scripted(questions: list[Question]) -> Script:
    """gpt-oss looks the figure up and is always right; DeepSeek reads the dataset and quotes it. From memory, gpt-oss
    names last year's period and DeepSeek gives no JSON at all."""
    by_text = {q.text: q for q in questions}

    def reply(model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> dict[str, Any]:
        q = by_text[messages[1]["content"]]
        if tools and not any(m["role"] == "tool" for m in messages):
            return {"role": "assistant", "content": "", "tool_calls": [tool_call("search_releases", query=q.text)]}
        if tools and model == MODELS[0]:
            return final(q.value, q.unit, q.period, q.release_url)
        if tools:
            return final(q.dataset_value, q.unit, q.dataset_period, "lfs_month")
        return final(q.value, q.unit, "2025-08", "memory") if model == MODELS[0] else {"role": "assistant", "content": "I am not sure."}
    return reply


@pytest.fixture(scope="session")
def answered(store: Store, questions: list[Question], tmp_path_factory: pytest.TempPathFactory) -> RunLog:
    """Every question asked of both models in both modes through the scripted fake, logged as a real run would be."""
    run_log = RunLog(tmp_path_factory.mktemp("runs"))
    run(FakeChat(scripted(questions)), store, questions, MODELS, run_log, store.taken, 0, sleep=lambda s: None)
    return run_log
