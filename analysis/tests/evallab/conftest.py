from pathlib import Path

import pytest

from evallab.store import Store, load

from .world import take_snapshot


@pytest.fixture(scope="session")
def store(tmp_path_factory: pytest.TempPathFactory) -> Store:
    """The synthetic snapshot, taken once and shared by every test that only reads it."""
    root: Path = tmp_path_factory.mktemp("snapshot")
    take_snapshot(root)
    return load(root)
