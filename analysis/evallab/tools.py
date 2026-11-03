"""The four tools a model may call, each reading only the frozen snapshot, and the baseline that trusts the open data."""

from __future__ import annotations

import inspect
import json
import logging
import re
from collections.abc import Callable
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

from .statistics import Statistic
from .store import Release, Store, latest

log = logging.getLogger(__name__)

MAX_RESULTS = 8
MAX_DATES = 12  # dates read_dataset returns at most
MAX_ROWS = 120
PAGE_CHARS = 6000  # text read_release returns from one page at most
STOPWORDS = frozenset("a an and the of for in on at to by with what is was are latest most recent malaysia malaysian berapakah terkini bagi di dan yang".split())


def tokens(text: str) -> frozenset[str]:
    return frozenset(t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1 and t not in STOPWORDS)


@cache
def page_tokens(path: Path) -> tuple[frozenset[str], ...]:
    return tuple(tokens(page) for page in json.loads(path.read_text("utf-8")))


def as_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def search_datasets(store: Store, query: str) -> list[dict[str, Any]]:
    wanted = tokens(query)
    scored = [(len(wanted & tokens(f"{d.id} {d.title} {d.title_ms} {d.description}")), d) for d in store.datasets.values()]
    best = sorted((s for s in scored if s[0] > 0), key=lambda s: (-s[0], not s[1].in_snapshot, s[1].id))[:MAX_RESULTS]
    return [{"id": d.id, "title": d.title, "frequency": d.frequency, "data_as_of": d.data_as_of, "in_snapshot": d.in_snapshot} for _, d in best]


def read_dataset(store: Store, id: str, last_n: Any = 3) -> dict[str, Any]:
    dataset = store.datasets.get(id)
    if dataset is None:
        return {"error": f"no dataset with id {id!r}; use search_datasets to find one"}
    if not dataset.in_snapshot:
        return {"error": f"dataset {id!r} is in the catalogue but not in this snapshot"}
    rows = store.rows(id)
    if not rows:
        return {"error": f"dataset {id!r} has no rows"}
    dates = sorted({r["date"] for r in rows})[-min(max(as_int(last_n, 3), 1), MAX_DATES):]
    chosen = [{**r, "date": r["date"].isoformat()} for r in rows if r["date"] in dates][-MAX_ROWS:]
    return {"id": id, "title": dataset.title, "frequency": dataset.frequency, "url": dataset.url, "columns": list(chosen[0]), "rows": chosen}


def release_score(store: Store, release: Release, wanted: frozenset[str]) -> tuple[int, list[int]]:
    """Twice the words matched in the title and summary, plus the best page; and the pages that match best."""
    head = len(wanted & tokens(f"{release.id} {release.title} {release.summary}"))
    if release.pages is None:
        return 2 * head, []
    per_page = [len(wanted & page) for page in page_tokens(store.root / release.pages)]
    best = max(per_page, default=0)
    return 2 * head + best, [i + 1 for i, n in enumerate(per_page) if n == best and n > 0][:3]


def search_releases(store: Store, query: str, after: str | None = None) -> list[dict[str, Any]] | dict[str, str]:
    if after:
        try:
            after = date.fromisoformat(after).isoformat()  # Python 3.12 also accepts 20260901 and 2026-W36-2; release dates are compared as YYYY-MM-DD text
        except ValueError:
            return {"error": f"after must be a YYYY-MM-DD date, not {after!r}"}
    wanted = tokens(query)
    candidates = [r for r in store.releases.values() if not after or r.date is None or r.date >= after]
    scored = [(release_score(store, r, wanted), r) for r in candidates]
    matched = sorted((s for s in scored if s[0][0] > 0), key=lambda s: s[1].id)
    newest_first = sorted(matched, key=lambda s: s[1].date or s[1].period, reverse=True)  # stable sorts: id, then recency, then the rank below
    best = sorted(newest_first, key=lambda s: (s[1].pages is None, -s[0][0]))  # releases with text in the snapshot come first
    return [{"id": r.id, "title": r.title, "agency": r.agency, "release_date": r.date, "in_snapshot": r.pages is not None, "matching_pages": pages}
            for (_, pages), r in best[:MAX_RESULTS]]


def read_release(store: Store, id: str, page: Any = 1) -> dict[str, Any]:
    release = store.releases.get(id)
    if release is None:
        return {"error": f"no release with id {id!r}; use search_releases to find one"}
    if release.pages is None:
        return {"error": f"release {id!r} is in the index but its text is not in this snapshot"}
    pages = store.pages(id)
    number = as_int(page, 1)
    if not 1 <= number <= len(pages):
        return {"error": f"page must be from 1 to {len(pages)}"}
    return {"id": id, "title": release.title, "release_date": release.date, "url": release.url, "page": number, "pages": len(pages), "text": pages[number - 1][:PAGE_CHARS]}


def _schema(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {"type": "object", "properties": properties, "required": required}}}


TOOLS = [
    _schema("search_datasets", "Search the data.gov.my catalogue. Returns dataset ids, titles, frequency and the latest period each dataset claims to cover.",
            {"query": {"type": "string", "description": "Words to look for, in English or Bahasa Malaysia"}}, ["query"]),
    _schema("read_dataset", "Read the newest rows of a data.gov.my dataset.",
            {"id": {"type": "string"}, "last_n": {"type": "integer", "description": f"How many of the newest dates to return, 1 to {MAX_DATES}"}}, ["id"]),
    _schema("search_releases", "Search official releases from DOSM, Bank Negara Malaysia and MYNIC. Returns release ids, dates and the pages that match best.",
            {"query": {"type": "string"}, "after": {"type": "string", "description": "Only releases on or after this YYYY-MM-DD date"}}, ["query"]),
    _schema("read_release", "Read one page of an official release's text.",
            {"id": {"type": "string"}, "page": {"type": "integer", "description": "Page number, starting at 1"}}, ["id"]),
]
HANDLERS: dict[str, Callable[..., Any]] = {"search_datasets": search_datasets, "read_dataset": read_dataset, "search_releases": search_releases, "read_release": read_release}


def call_tool(store: Store, name: str, arguments: Any) -> str:
    """Run one tool call and return its result as JSON text. A bad call or a failing handler comes back as an error the model can read, never as an exception."""
    handler = HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"unknown tool {name!r}"})
    kwargs = arguments if isinstance(arguments, dict) else {}
    try:
        inspect.signature(handler).bind(store, **kwargs)
    except TypeError as err:
        return json.dumps({"error": f"bad arguments for {name}: {err}"})
    try:
        return json.dumps(handler(store, **kwargs), ensure_ascii=False, default=str)
    except Exception as err:  # noqa: BLE001 - one bad call must not abort a long run; the model sees the message instead
        log.warning("tool %s failed with arguments %r", name, kwargs, exc_info=True)
        return json.dumps({"error": f"{name} failed: {type(err).__name__}: {err}. Check the argument types and try again."}, ensure_ascii=False)


def baseline_answer(store: Store, statistic: Statistic) -> str:
    """What a user gets by trusting the open data: the dataset's newest value and period, as a final answer."""
    found = latest(store, statistic.series, statistic.quarterly)
    if found is None:
        raise ValueError(f"{statistic.id}: dataset {statistic.series.dataset} has no value for this series")
    value, period = found
    return json.dumps({"value": round(value, statistic.decimals), "unit": statistic.unit, "period": period, "source": statistic.series.dataset})
