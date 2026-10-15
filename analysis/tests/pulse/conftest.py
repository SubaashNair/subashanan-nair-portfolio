import pytest

from pulse.pipeline import PulseRun, run

from .world import write_inputs


@pytest.fixture(scope="session")
def pulse_run(tmp_path_factory: pytest.TempPathFactory) -> PulseRun:
    """One full pipeline run on the synthetic world, shared by the pipeline and CLI tests."""
    return run(write_inputs(tmp_path_factory.mktemp("world")))
