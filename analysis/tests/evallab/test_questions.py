import csv
from dataclasses import replace
from pathlib import Path

import pytest

from evallab.questions import CURRENT, OUT_OF_DATE, draft, draft_all, read_questions, sheet_rows, write_sheet
from evallab.store import Store

from .world import STATS

BY_ID = {s.id: s for s in STATS}


def test_drafts_come_from_the_newest_release_and_are_compared_with_the_dataset(store: Store) -> None:
    drafts = {d.statistic.id: d for d in draft_all(store, STATS)}
    summary = {k: (d.value, d.period, d.release.id, d.dataset_period, d.status) for k, d in drafts.items()}
    assert summary == {
        "unemployment_rate": (2.9, "2026-08", "labour_month_2026-08", "2026-08", CURRENT),
        "youth_rate_15_24": (10.1, "2026-08", "labour_month_2026-08", "2026-06", OUT_OF_DATE),
        "m3": (pytest.approx(2636.548767), "2026-08", "bnm_mhs_2026-08_table_1.3", "2026-06", OUT_OF_DATE),
        "domains_active": (693122.0, "2026-09", "mynic_active_2026", "2025-01", OUT_OF_DATE),
    }
    assert drafts["unemployment_rate"].evidence == "unemployment rate for August 2026 eased to 2.9 per cent"


def test_the_review_sheet_has_four_questions_per_statistic(store: Store) -> None:
    rows = sheet_rows(draft_all(store, STATS))
    assert [r["id"] for r in rows] == [f"q{i:03d}" for i in range(1, 17)]
    assert [r["language"] for r in rows[:4]] == ["en", "en", "ms", "ms"]
    assert rows[0]["question"] == "What is Malaysia's latest unemployment rate?"
    assert rows[10]["question"] == "Berapakah penawaran wang M3 terkini bagi Malaysia?"
    m3 = rows[8]
    assert (m3["value"], m3["unit"], m3["dataset_value"], m3["release_url"]) == ("2636.5", "RM billion", "2670.4", "https://www.bnm.gov.my/documents/20124/999/1.3.xlsx")
    assert all(r["verified"] == "" for r in rows)


def test_a_release_without_the_headline_leaves_the_value_for_the_reviewer(store: Store) -> None:
    blind = replace(BY_ID["unemployment_rate"], pattern=r"nothing like this (?P<value>\d+)")
    d = draft(store, blind)
    assert d.value is None and d.evidence == "No match in the release text; read the release."
    assert sheet_rows([d])[0]["value"] == ""


def test_a_dataset_newer_than_the_release_is_flagged_and_counts_as_current(store: Store) -> None:
    d = draft(store, replace(BY_ID["unemployment_rate"], release=r"^labour_month_2026-06$"))
    assert (d.period, d.dataset_period, d.status) == ("2026-06", "2026-08", CURRENT)
    assert d.evidence.startswith("Dataset is newer than the latest release; check by hand.")


def test_a_set_with_nothing_out_of_date_is_refused(store: Store) -> None:
    with pytest.raises(ValueError, match="needs both current and out-of-date series; 0 of 1"):
        draft_all(store, [BY_ID["unemployment_rate"]])


def test_drafting_again_never_overwrites_the_sheet_by_accident(tmp_path: Path, store: Store) -> None:
    path = tmp_path / "questions.csv"
    rows = sheet_rows(draft_all(store, STATS))
    write_sheet(path, rows)
    path.write_text(path.read_text().replace(",\n", ",yes\n", 1))  # the reviewer has verified the first row
    with pytest.raises(FileExistsError, match="may hold verified answers"):
        write_sheet(path, rows)
    assert ",yes\n" in path.read_text()
    write_sheet(path, rows, force=True)
    assert ",yes\n" not in path.read_text()


def verified(tmp_path: Path, store: Store, edit: dict[str, str] | None = None) -> Path:
    rows = [{**r, "verified": "Yes "} for r in sheet_rows(draft_all(store, STATS))]
    rows[0] = {**rows[0], **(edit or {})}
    path = tmp_path / "questions.csv"
    write_sheet(path, rows, force=True)
    return path


def test_the_runner_reads_only_a_fully_verified_sheet(tmp_path: Path, store: Store) -> None:
    questions = read_questions(verified(tmp_path, store), STATS)
    assert len(questions) == 16 and (questions[4].value, questions[4].period, questions[4].status) == (10.1, "2026-08", OUT_OF_DATE)
    with pytest.raises(ValueError, match=r"1 of 16 questions are not verified yet \(q001\)"):
        read_questions(verified(tmp_path, store, {"verified": ""}), STATS)


@pytest.mark.parametrize(("edit", "message"), [
    ({"value": ""}, "q001: value '' is not a number"),
    ({"period": "August 2026"}, "q001: period 'August 2026' must look like 2026-08"),
    ({"statistic": "gdp"}, "q001: unknown statistic 'gdp'"),
])
def test_a_malformed_verified_row_stops_the_run(tmp_path: Path, store: Store, edit: dict[str, str], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        read_questions(verified(tmp_path, store, edit), STATS)


def test_values_with_thousands_separators_are_read(tmp_path: Path, store: Store) -> None:
    path = verified(tmp_path, store)
    rows = list(csv.DictReader(path.open()))
    rows[12]["value"] = "693,122"
    write_sheet(path, rows, force=True)
    assert read_questions(path, STATS)[12].value == 693122.0
