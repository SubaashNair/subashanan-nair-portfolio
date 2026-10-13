import json
import zipfile
from pathlib import Path

import numpy as np
import pytest

from forecasting import data
from forecasting.data import Block, load, make_split, sha256_of

from .conftest import ADJACENCY, STEPS, calendar_cells, synthetic_series, write_mat


def test_sha256_of_matches_a_known_digest(tmp_path: Path) -> None:
    path = tmp_path / "x.txt"
    path.write_bytes(b"abc")
    assert sha256_of(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_load_reads_series_and_adjacency(tiny: data.Traffic) -> None:
    assert tiny.series.shape == (4, STEPS)
    assert tiny.adjacency.shape == (4, 4)
    assert tiny.series.min() >= 0 and tiny.series.max() <= 1


def test_load_rejects_a_calendar_that_does_not_match_the_steps(tmp_path: Path) -> None:
    cells = calendar_cells(STEPS)
    cells[0, 200] = cells[0, 300]
    with pytest.raises(ValueError, match="step 200"):
        load(write_mat(tmp_path / "bad.mat", synthetic_series(), cells=cells))


def test_load_rejects_a_sensor_with_no_neighbours(tmp_path: Path) -> None:
    lonely = ADJACENCY.copy()
    lonely[0, 1] = lonely[1, 0] = 0
    with pytest.raises(ValueError, match="neighbour"):
        load(write_mat(tmp_path / "lonely.mat", synthetic_series(), adjacency=lonely))


def test_split_is_ordered_contiguous_and_non_overlapping() -> None:
    split = make_split(1261)
    assert split.train == Block(0, 864)
    assert split.val == Block(864, 1056)
    assert split.test == Block(1056, 1261)
    assert split.train.stop == split.val.start and split.val.stop == split.test.start
    assert set(range(*split.train.as_list())).isdisjoint(range(*split.test.as_list()))


def test_split_needs_a_test_block() -> None:
    with pytest.raises(ValueError):
        make_split(1056)


def test_fetch_reuses_the_cache_without_the_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with zipfile.ZipFile(tmp_path / data.ZIP_NAME, "w") as archive:
        archive.writestr(data.MAT_NAME, b"mat bytes")
    (tmp_path / data.RETRIEVED_NAME).write_text(json.dumps({"retrieved": "2026-10-13T01:02:03+00:00"}))

    def no_network(*_: object) -> None:
        raise AssertionError("fetch went to the network")

    monkeypatch.setattr(data.urllib.request, "urlretrieve", no_network)
    raw = data.fetch(tmp_path)
    assert raw.mat_path.read_bytes() == b"mat bytes"
    assert raw.retrieved == "2026-10-13T01:02:03+00:00"


def test_calendar_helpers_follow_the_publisher_fields() -> None:
    assert (data.weekday_of(0), data.hour_of(0)) == (0, 0)
    assert (data.weekday_of(95), data.hour_of(95)) == (0, 23)
    assert (data.weekday_of(96 * 5), data.hour_of(96 * 5 + 4)) == (0, 1)
    assert np.isclose(data.STEP_MINUTES * data.STEPS_PER_DAY, 24 * 60)
