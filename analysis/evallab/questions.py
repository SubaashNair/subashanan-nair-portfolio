"""Draft each statistic's correct answer from its latest release, write the review sheet, and read it back once verified."""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .sources import bnm_latest, mynic_points
from .statistics import Statistic
from .store import Release, Store, latest

log = logging.getLogger(__name__)

QUESTIONS_PATH = Path(__file__).with_name("questions.csv")
FIELDS = ["id", "statistic", "agency", "language", "question", "value", "unit", "period", "release_id", "release_url",
          "dataset_id", "dataset_value", "dataset_period", "status", "evidence", "verified"]
TEMPLATES = (
    ("en", "What is Malaysia's latest {en}?"),
    ("en", "According to the most recent official figures, what was the {en} in Malaysia, and for which period?"),
    ("ms", "Berapakah {ms} terkini bagi Malaysia?"),
    ("ms", "Menurut angka rasmi terbaru, berapakah {ms} di Malaysia, dan bagi tempoh mana?"),
)
CURRENT, OUT_OF_DATE = "current", "out of date"
FEW_OUT_OF_DATE = 6  # fewer out-of-date statistics than this makes the headline view thin
PERIOD = {False: re.compile(r"^\d{4}-(0[1-9]|1[0-2])$"), True: re.compile(r"^\d{4}-Q[1-4]$")}


@dataclass(frozen=True)
class Draft:
    statistic: Statistic
    value: float | None  # None when the release text did not give it up; the reviewer fills it in
    period: str
    release: Release
    dataset_value: float
    dataset_period: str
    evidence: str

    @property
    def status(self) -> str:
        return OUT_OF_DATE if self.dataset_period < self.period else CURRENT


@dataclass(frozen=True)
class Question:
    id: str
    statistic: str
    language: str
    text: str
    value: float
    unit: str
    period: str
    release_url: str
    dataset_value: float
    dataset_period: str
    status: str


def frozen_releases(store: Store, s: Statistic, test: str) -> list[Release]:
    """Releases with text in the snapshot whose id matches, newest first."""
    chosen = [r for r in store.releases.values() if r.agency == s.agency and r.pages is not None and re.search(test, r.id)]
    if not chosen:
        raise ValueError(f"{s.id}: no {s.agency} release in the snapshot matches {test}")
    return sorted(chosen, key=lambda r: (r.date or "", r.period, r.id), reverse=True)


def from_release(store: Store, s: Statistic) -> tuple[float | None, str, Release, str]:
    """The figure, its period, the release it comes from and the evidence for the reviewer."""
    if s.agency == "DOSM":
        release = frozen_releases(store, s, s.release)[0]
        match = re.search(s.pattern, " ".join(store.pages(release.id)))
        evidence = match[0][:300] if match else "No match in the release text; read the release."
        return (float(match["value"].replace(",", "")) if match else None), release.period, release, evidence
    if s.agency == "BNM":
        table, column = s.release.split(":")
        release = frozen_releases(store, s, rf"_table_{re.escape(table)}$")[0]
        found = bnm_latest(store.root / str(release.raw), int(column))
        if found is None:
            raise ValueError(f"{s.id}: table {table} has no value")
        column_letter = chr(ord("A") + int(column))  # BNM column index is 0-based, so A is the first blank index
        return found[0] * s.release_scale, found[1], release, f"Table {table}, column {column_letter}, row {found[1]}"
    points = [(period, total, r) for r in frozen_releases(store, s, rf"^mynic_{s.release}_\d{{4}}$") for period, total in mynic_points(store.root / str(r.raw))]
    if not points:
        raise ValueError(f"{s.id}: the MYNIC {s.release} chart has no months with data")
    period, total, release = max(points, key=lambda p: p[0])
    return float(total), period, release, f"MYNIC {s.release} domains chart, {period}"


def draft(store: Store, s: Statistic) -> Draft:
    in_dataset = latest(store, s.series, s.quarterly)
    if in_dataset is None:
        raise ValueError(f"{s.id}: dataset {s.series.dataset} has no value for this series")
    value, period, release, evidence = from_release(store, s)
    if in_dataset[1] > period:
        evidence = f"Dataset is newer than the latest release; check by hand. {evidence}"
    return Draft(s, value, period, release, in_dataset[0], in_dataset[1], evidence)


def draft_all(store: Store, statistics: list[Statistic]) -> list[Draft]:
    drafts = [draft(store, s) for s in statistics]
    stale = sum(d.status == OUT_OF_DATE for d in drafts)
    if stale == 0 or stale == len(drafts):
        raise ValueError(f"the question set needs both current and out-of-date series; {stale} of {len(drafts)} statistics are out of date")
    if stale < FEW_OUT_OF_DATE:
        log.warning("only %d statistics are out of date; the headline view will be thin", stale)
    return drafts


def fixed(value: float | None, decimals: int) -> str:
    return "" if value is None else f"{value:.{decimals}f}"


def sheet_rows(drafts: list[Draft]) -> list[dict[str, str]]:
    rows = []
    for d in drafts:
        s = d.statistic
        for language, template in TEMPLATES:
            rows.append({
                "id": f"q{len(rows) + 1:03d}", "statistic": s.id, "agency": s.agency, "language": language,
                "question": template.format(en=s.name_en, ms=s.name_ms), "value": fixed(d.value, s.decimals), "unit": s.unit, "period": d.period,
                "release_id": d.release.id, "release_url": d.release.url, "dataset_id": s.series.dataset,
                "dataset_value": fixed(d.dataset_value, s.decimals), "dataset_period": d.dataset_period, "status": d.status, "evidence": d.evidence, "verified": "",
            })
    return rows


def write_sheet(path: Path, rows: list[dict[str, str]], force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists and may hold verified answers; pass --force to replace it")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_row(row: dict[str, str], statistics: dict[str, Statistic]) -> Question:
    s = statistics.get(row["statistic"])
    if s is None:
        raise ValueError(f"{row['id']}: unknown statistic {row['statistic']!r}")
    if not PERIOD[s.quarterly].match(row["period"]):
        raise ValueError(f"{row['id']}: period {row['period']!r} must look like {'2026-Q2' if s.quarterly else '2026-08'}")
    try:
        value = float(row["value"].replace(",", ""))
    except ValueError:
        raise ValueError(f"{row['id']}: value {row['value']!r} is not a number") from None
    return Question(row["id"], s.id, row["language"], row["question"], value, s.unit, row["period"], row["release_url"],
                    float(row["dataset_value"]), row["dataset_period"], row["status"])


def read_questions(path: Path, statistics: list[Statistic]) -> list[Question]:
    """The verified question set. Refuses to return anything while a single row is unverified or malformed."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    waiting = [r["id"] for r in rows if r["verified"].strip().lower() != "yes"]
    if waiting:
        raise ValueError(f"{len(waiting)} of {len(rows)} questions are not verified yet ({', '.join(waiting[:5])}); check each against its release and set verified to yes")
    by_id = {s.id: s for s in statistics}
    return [parse_row(r, by_id) for r in rows]
