from pathlib import Path

import pytest

from evallab.questions import Question, draft_all, read_questions, sheet_rows, write_sheet
from evallab.store import Store, load

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
