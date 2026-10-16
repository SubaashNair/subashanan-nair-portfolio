"""The frozen snapshot, read back for the tools, the baseline and the answer drafts. Nothing here touches the network."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .snapshot import OPENDOSM_PAGE, read_catalogue, verify
from .statistics import Series, period_of


@dataclass(frozen=True)
class Dataset:
    id: str
    title: str
    title_ms: str
    description: str
    frequency: str
    data_as_of: str
    url: str  # the parquet file on data.gov.my storage
    in_snapshot: bool


@dataclass(frozen=True)
class Release:
    id: str
    agency: str
    title: str
    date: str | None  # release date, when the publisher gives one
    period: str
    summary: str  # what the release covers, searched with the title
    url: str  # the file the figures come from
    page: str  # the web page that lists it
    raw: str | None  # the downloaded file in the snapshot, None when only the index entry is known
    pages: str | None  # its text, page by page


@dataclass(frozen=True)
class Store:
    root: Path
    taken: str
    commit: str
    datasets: dict[str, Dataset]
    releases: dict[str, Release]  # every DOSM release in the index, plus the BNM and MYNIC ones in the snapshot

    def rows(self, dataset_id: str) -> list[dict[str, Any]]:
        """Every row of a dataset in the snapshot, oldest first, with dates as datetime.date."""
        return read_rows(self.root / f"datasets/{dataset_id}.parquet")

    def pages(self, release_id: str) -> list[str]:
        release = self.releases[release_id]
        if release.pages is None:
            raise KeyError(f"{release_id} is listed in the release index but its text is not in the snapshot")
        return json.loads((self.root / release.pages).read_text("utf-8"))

    def sources(self) -> frozenset[str]:
        """Every dataset id and URL an answer may cite."""
        urls = {u for r in self.releases.values() if r.pages is not None for u in (r.url, r.page)}
        return frozenset({d.id for d in self.datasets.values() if d.in_snapshot} | {d.url for d in self.datasets.values() if d.in_snapshot} | urls)


@cache
def read_rows(path: Path) -> list[dict[str, Any]]:
    """Parquet dates arrive as date or as timestamp depending on the file; both become datetime.date."""
    as_date = lambda d: d.date() if isinstance(d, datetime) else d  # noqa: E731
    return sorted(({**row, "date": as_date(row["date"])} for row in pq.read_table(path).to_pylist()), key=lambda r: r["date"])


def load(root: Path) -> Store:
    snapshot = verify(root)
    catalogue, index = read_catalogue(root / "catalogue.tar.gz")
    saved = {p.stem for p in (root / "datasets").glob("*.parquet")}
    datasets = {
        key: Dataset(key, m.get("title_en", key), m.get("title_ms", ""), m.get("description_en", ""), m.get("frequency", ""), str(m.get("data_as_of", "")),
                     m.get("link_parquet", ""), key in saved)
        for key, m in catalogue.items()
    }
    frozen = {r["id"]: Release(r["id"], r["agency"], r["title"], r["date"], r["period"], r["summary"], r["url"], r["page"], r["raw"], r["pages"])
              for r in snapshot["releases"]}
    listed = {
        r["publication"]: Release(r["publication"], "DOSM", r["en"]["title"], r["release_date"], "", r["en"].get("description", ""),
                                  r["en"]["resources"][0]["resource_link"], OPENDOSM_PAGE.format(id=r["publication"]), None, None)
        for r in index
    }
    return Store(root, snapshot["taken"], snapshot["catalogue"]["commit"], datasets, {**listed, **frozen})


def latest(store: Store, series: Series, quarterly: bool) -> tuple[float, str] | None:
    """The newest value of a series in its dataset, scaled to the statistic's unit, with its period."""
    rows = [r for r in store.rows(series.dataset) if all(str(r.get(k)) == v for k, v in series.where) and r.get(series.column) is not None]
    if not rows:
        return None
    row = rows[-1]
    return float(row[series.column]) * series.scale, period_of(row["date"], quarterly)
