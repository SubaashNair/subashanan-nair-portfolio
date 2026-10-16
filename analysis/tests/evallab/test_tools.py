import json
from typing import Any

import pytest

from evallab import tools
from evallab.statistics import STATISTICS
from evallab.store import Store, latest
from evallab.tools import TOOLS, baseline_answer, call_tool, read_dataset, read_release, search_datasets, search_releases

BY_ID = {s.id: s for s in STATISTICS}


def test_the_store_lists_the_whole_catalogue_and_marks_what_was_downloaded(store: Store) -> None:
    assert store.taken == "2026-10-15"
    assert store.datasets["lfs_month_youth"].in_snapshot and not store.datasets["cpi_headline"].in_snapshot
    assert store.releases["labour_month_2026-05"].pages is None and store.releases["labour_month_2026-08"].pages is not None


@pytest.mark.parametrize(("statistic", "expected"), [
    ("youth_rate_15_24", (10.2, "2026-06")),
    ("m3", (pytest.approx(2670.359957), "2026-06")),  # timestamp dates, scaled from RM million to RM billion
    ("domains_active", (352717.0, "2025-01")),  # the overall cumulative row, not .my alone or the net new count
])
def test_latest_reads_the_newest_value_of_one_series(store: Store, statistic: str, expected: tuple) -> None:
    s = BY_ID[statistic]
    assert latest(store, s.series, s.quarterly) == expected


def test_search_datasets_ranks_by_matching_words(store: Store) -> None:
    found = search_datasets(store, "youth unemployment")
    assert found[0] == {"id": "lfs_month_youth", "title": "Monthly Youth Unemployment", "frequency": "MONTHLY", "data_as_of": "2026-06", "in_snapshot": True}
    assert search_datasets(store, "the latest") == []  # only stop words


def test_read_dataset_returns_the_newest_dates(store: Store) -> None:
    newest = read_dataset(store, "lfs_month", 1)
    assert newest["rows"] == [{"date": "2026-08-01", "u_rate": 2.9}] and newest["columns"] == ["date", "u_rate"]
    assert len(read_dataset(store, "lfs_month", "two")["rows"]) == 3  # an unreadable count falls back to 3
    assert "not in this snapshot" in read_dataset(store, "cpi_headline")["error"]
    assert "no dataset" in read_dataset(store, "nope")["error"]


def test_search_releases_puts_the_newest_matching_release_first(store: Store) -> None:
    found = search_releases(store, "labour force unemployment rate")
    assert [r["id"] for r in found[:4]] == ["labour_month_2026-08", "labour_month_2026-07", "labour_month_2026-06", "labour_month_2026-05"]
    assert found[3]["in_snapshot"] is False
    assert search_releases(store, "youth unemployment rate")[0]["matching_pages"] == [2]
    assert [r["id"] for r in search_releases(store, "labour force", after="2026-09-01")] == ["labour_month_2026-08", "labour_month_2026-07"]
    assert search_releases(store, "money supply M3")[0]["id"] == "bnm_mhs_2026-08_table_1.3"
    assert [r["id"] for r in search_releases(store, "active .my domains")] == ["mynic_active_2026", "mynic_active_2025"]  # undated: newest year first
    assert "YYYY-MM-DD" in search_releases(store, "labour", after="last month")["error"]


def test_read_release_returns_one_page(store: Store) -> None:
    page = read_release(store, "labour_month_2026-08", 2)
    assert page["pages"] == 2 and "eased to 2.9 per cent" in page["text"] and page["url"].endswith("lfs_2026-08_en.pdf")
    assert read_release(store, "labour_month_2026-08", 3)["error"] == "page must be from 1 to 2"
    assert "not in this snapshot" in read_release(store, "labour_month_2026-05")["error"]


def test_call_tool_turns_bad_calls_into_errors_the_model_can_read(store: Store) -> None:
    assert json.loads(call_tool(store, "read_release", {"id": "mynic_active_2026"}))["text"].startswith("MYNIC domain statistics")
    assert json.loads(call_tool(store, "delete_everything", {})) == {"error": "unknown tool 'delete_everything'"}
    assert "bad arguments for search_datasets" in json.loads(call_tool(store, "search_datasets", {"q": "cpi"}))["error"]
    assert "bad arguments" in json.loads(call_tool(store, "read_dataset", "lfs_month"))["error"]
    assert [t["function"]["name"] for t in TOOLS] == ["search_datasets", "read_dataset", "search_releases", "read_release"]


@pytest.mark.parametrize(("name", "arguments"), [
    ("search_datasets", {"query": 5}),  # wrong type
    ("search_releases", {"query": "labour", "after": 5}),  # wrong type
    ("search_releases", {"after": "2026-01-01"}),  # missing required argument
    ("read_release", {"id": ["a"]}),  # unhashable id
    ("read_dataset", {"id": {"x": 1}}),
])
def test_call_tool_never_raises_for_wrongly_typed_or_missing_arguments(store: Store, name: str, arguments: dict[str, Any]) -> None:
    assert "error" in json.loads(call_tool(store, name, arguments))


def test_call_tool_turns_a_crashing_handler_into_an_error(store: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(store: Store, query: str) -> list[Any]:
        raise RuntimeError("disk on fire")

    monkeypatch.setitem(tools.HANDLERS, "search_datasets", broken)
    result = json.loads(call_tool(store, "search_datasets", {"query": "cpi"}))
    assert "search_datasets failed" in result["error"] and "disk on fire" in result["error"]


def test_the_baseline_trusts_the_open_dataset(store: Store) -> None:
    assert json.loads(baseline_answer(store, BY_ID["youth_rate_15_24"])) == {"value": 10.2, "unit": "per cent", "period": "2026-06", "source": "lfs_month_youth"}
    assert json.loads(baseline_answer(store, BY_ID["m3"]))["value"] == 2670.4


def test_an_answer_may_cite_any_dataset_or_release_in_the_snapshot(store: Store) -> None:
    sources = store.sources()
    assert {"lfs_month_youth", "https://open.dosm.gov.my/publications/labour_month_2026-08", "https://www.bnm.gov.my/documents/20124/999/1.3.xlsx"} <= sources
    assert "cpi_headline" not in sources and "https://open.dosm.gov.my/publications/labour_month_2026-05" not in sources


def test_after_accepts_any_iso_form_and_filters_the_same_way(store: Store) -> None:
    expected = [r["id"] for r in search_releases(store, "labour force", after="2026-09-01")]
    assert expected == ["labour_month_2026-08", "labour_month_2026-07"]
    for form in ("20260901", "2026-W36-2"):  # ISO basic date; ISO week date (Tuesday of week 36 is 2026-09-01)
        assert [r["id"] for r in search_releases(store, "labour force", after=form)] == expected


@pytest.mark.parametrize("bad_id", ["../manifest.json", "/etc/passwd", ".."])
def test_ids_shaped_like_paths_are_just_unknown_ids(store: Store, monkeypatch: pytest.MonkeyPatch, bad_id: str) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a file was read")

    monkeypatch.setattr(Store, "rows", forbidden)
    monkeypatch.setattr(Store, "pages", forbidden)
    assert "no dataset" in read_dataset(store, bad_id)["error"]
    assert "no release" in read_release(store, bad_id)["error"]


def test_a_dataset_in_the_snapshot_with_no_rows_is_an_error_not_a_crash(store: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Store, "rows", lambda self, dataset_id: [])
    assert read_dataset(store, "lfs_month")["error"] == "dataset 'lfs_month' has no rows"
    assert json.loads(call_tool(store, "read_dataset", {"id": "lfs_month"}))["error"] == "dataset 'lfs_month' has no rows"
