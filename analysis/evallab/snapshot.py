"""Take the study's snapshot once: catalogue, datasets, DOSM releases, BNM tables and MYNIC charts, each with its checksum.

Later runs only verify the files against snapshot.json, so every run after the first reads exactly the same bytes.
"""

from __future__ import annotations

import json
import logging
import re
import tarfile
import time
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime
from email.message import Message
from pathlib import Path
from typing import IO, Any

from forecasting.data import sha256_of

from .sources import bnm_text, dosm_period, latest_edition, mynic_text, pdf_pages, table_link
from .statistics import Statistic

log = logging.getLogger(__name__)

Get = Callable[[str], bytes]

USER_AGENT = "observatory-analysis/0.1 (LLM Eval Lab study)"
POLITE_SECONDS = 0.5  # pause before every request
REPO = "data-gov-my/datagovmy-meta"
HEAD_URL = f"https://api.github.com/repos/{REPO}/commits/HEAD"
TARBALL_URL = "https://codeload.github.com/" + REPO + "/tar.gz/{commit}"
BNM_LISTING = "https://www.bnm.gov.my/publications/mhs"
MYNIC_URL = "https://mynic.my/ajax/statistics?type={chart}&year={year}"
MYNIC_PAGE = "https://mynic.my/media/statistics"
OPENDOSM_PAGE = "https://open.dosm.gov.my/publications/{id}"
RELEASES_PER_SERIES = 3  # the newest DOSM releases kept for each release series
SNAPSHOT = "snapshot.json"
ALLOWED_HOSTS = frozenset({"api.github.com", "codeload.github.com", "storage.data.gov.my", "storage.dosm.gov.my", "open.dosm.gov.my", "www.bnm.gov.my", "mynic.my"})
SAFE_ID = re.compile(r"[A-Za-z0-9._-]+")  # what a release or dataset id may contain once it becomes part of a file name
HTTPS_PORT = 443


def check_url(url: str) -> str:
    """The URL, if it is https, on a publisher's host, with no userinfo and no unusual port. Links in downloaded data pass through here."""
    if re.search(r"[\s\x00-\x1f\x7f]", url):  # urlsplit silently drops tabs and newlines, so a URL holding them would not be the URL that is requested
        raise ValueError(f"refusing to fetch {url!r}: it contains whitespace or control characters")
    parts = urllib.parse.urlsplit(url)
    try:
        port = parts.port
    except ValueError:
        port = -1
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS or "@" in parts.netloc or port not in (None, HTTPS_PORT):
        raise ValueError(f"refusing to fetch {url!r}: only https URLs on {', '.join(sorted(ALLOWED_HOSTS))} are allowed")
    return url


class CheckedRedirects(urllib.request.HTTPRedirectHandler):
    """Follows a redirect only to a URL that passes check_url, so an allowed host cannot send the fetch to a local or internal address."""

    def redirect_request(self, req: urllib.request.Request, fp: IO[bytes], code: int, msg: str, headers: Message, newurl: str) -> urllib.request.Request | None:
        return super().redirect_request(req, fp, code, msg, headers, check_url(newurl))


def opener() -> urllib.request.OpenerDirector:
    """Its own opener, never installed globally: other code in the process keeps plain urlopen (the Ollama client uses http://localhost)."""
    return urllib.request.build_opener(CheckedRedirects)


def safe_id(value: str) -> str:
    if not SAFE_ID.fullmatch(value):
        raise ValueError(f"{value!r} is not a safe file name: use only letters, digits, '.', '_' and '-'")
    return value


def http_get(url: str) -> bytes:
    check_url(url)
    time.sleep(POLITE_SECONDS)
    headers = {"User-Agent": USER_AGENT}
    if url == HEAD_URL:
        headers["Accept"] = "application/vnd.github.sha"  # the commit SHA as plain text
    with opener().open(urllib.request.Request(url, headers=headers), timeout=300) as response:
        return response.read()


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class Freezer:
    """Writes files into the raw directory and remembers what each one is, for snapshot.json."""

    def __init__(self, raw_dir: Path, get: Get) -> None:
        self.raw_dir, self.get, self.files = raw_dir.resolve(), get, []

    def fetch(self, url: str, name: str) -> Path:
        log.info("fetching %s", url)
        return self.save(name, self.get(url), url)

    def save(self, name: str, data: bytes, url: str | None) -> Path:
        path = (self.raw_dir / name).resolve()
        if self.raw_dir not in path.parents:
            raise ValueError(f"refusing to write {name!r}: it resolves outside {self.raw_dir}")
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(path.name + ".part")
        partial.write_bytes(data)
        partial.replace(path)
        self.files.append({"path": path.relative_to(self.raw_dir).as_posix(), "url": url, "retrieved": now(), "bytes": len(data), "sha256": sha256_of(path)})
        return path

    def pages(self, release_id: str, pages: list[str]) -> str:
        name = f"releases/{safe_id(release_id)}.pages.json"
        self.save(name, json.dumps(pages, ensure_ascii=False, indent=0).encode(), None)
        return name


def read_catalogue(tarball: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Dataset metadata by id, and every DOSM release record, from the metadata repository's tarball."""
    datasets, releases = {}, []
    with tarfile.open(tarball) as archive:
        for member in archive.getmembers():
            parts = member.name.split("/")
            if not member.isfile() or not member.name.endswith(".json"):
                continue
            if parts[1:2] == ["data-catalogue"] and len(parts) == 3:
                datasets[parts[2][:-5]] = json.load(archive.extractfile(member))
            elif parts[1:3] == ["pub-dosm", "publications"] and len(parts) == 4:
                releases.append(json.load(archive.extractfile(member)))
    return datasets, releases


def newest_releases(index: list[dict[str, Any]], pattern: str) -> list[dict[str, Any]]:
    chosen = [r for r in index if re.match(pattern, r["publication"])]
    if not chosen:
        raise ValueError(f"no DOSM release matches {pattern}")
    return sorted(chosen, key=lambda r: (r["release_date"], r["publication"]), reverse=True)[:RELEASES_PER_SERIES]


def english_pdf(record: dict[str, Any]) -> str:
    return next(r["resource_link"] for r in record["en"]["resources"] if r["resource_type"] == "pdf")


def freeze_dosm(f: Freezer, index: list[dict[str, Any]], patterns: Iterable[str]) -> list[dict[str, Any]]:
    entries = []
    for record in [r for p in sorted(set(patterns)) for r in newest_releases(index, p)]:
        rid, url = safe_id(record["publication"]), english_pdf(record)
        raw = f.fetch(url, f"releases/{rid}.pdf")
        entries.append({"id": rid, "agency": "DOSM", "title": record["en"]["title"], "date": record["release_date"], "period": dosm_period(rid),
                        "summary": record["en"].get("description", ""), "url": url, "page": OPENDOSM_PAGE.format(id=rid), "raw": str(raw.relative_to(f.raw_dir)), "pages": f.pages(rid, pdf_pages(raw))})
    return entries


def freeze_bnm(f: Freezer, statistics: list[Statistic]) -> list[dict[str, Any]]:
    edition_url, period = latest_edition(f.fetch(BNM_LISTING, "releases/bnm_mhs_listing.html").read_text("utf-8"))
    edition = f.fetch(edition_url, f"releases/bnm_mhs_{safe_id(period)}_edition.html").read_text("utf-8")
    entries = []
    for table in sorted({s.release.split(":")[0] for s in statistics}):
        columns = {int(s.release.split(":")[1]): s.name_en for s in statistics if s.release.startswith(table + ":")}
        rid, url = safe_id(f"bnm_mhs_{period}_table_{table}"), table_link(edition, table)
        raw = f.fetch(url, f"releases/{rid}.xlsx")
        title = f"Bank Negara Malaysia, Monthly Highlights and Statistics for {period}, table {table}"
        entries.append({"id": rid, "agency": "BNM", "title": title, "date": None, "period": period, "summary": "; ".join(columns.values()), "url": url, "page": edition_url,
                        "raw": str(raw.relative_to(f.raw_dir)), "pages": f.pages(rid, [bnm_text(raw, table, columns)])})
    return entries


def freeze_mynic(f: Freezer, statistics: list[Statistic], today: date) -> list[dict[str, Any]]:
    entries = []
    for chart in sorted({s.release for s in statistics}):
        summary = "; ".join(s.name_en for s in statistics if s.release == chart)
        for year in (today.year, today.year - 1):  # last year too, so January still has a latest month
            rid, url = safe_id(f"mynic_{chart}_{year}"), MYNIC_URL.format(chart=chart, year=year)
            raw = f.fetch(url, f"releases/{rid}.json")
            entries.append({"id": rid, "agency": "MYNIC", "title": f"MYNIC domain statistics, {chart} domains, {year}", "date": None, "period": str(year),
                            "summary": summary, "url": url, "page": MYNIC_PAGE, "raw": str(raw.relative_to(f.raw_dir)), "pages": f.pages(rid, [mynic_text(raw, chart)])})
    return entries


def take(raw_dir: Path, statistics: list[Statistic], today: date, get: Get) -> dict[str, Any]:
    f = Freezer(raw_dir, get)
    commit = get(HEAD_URL).decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(f"unexpected commit from GitHub: {commit[:80]!r}")
    tarball = f.fetch(TARBALL_URL.format(commit=commit), "catalogue.tar.gz")
    catalogue, index = read_catalogue(tarball)
    for dataset in sorted({s.series.dataset for s in statistics}):
        f.fetch(catalogue[dataset]["link_parquet"], f"datasets/{safe_id(dataset)}.parquet")
    by_agency = {a: [s for s in statistics if s.agency == a] for a in ("DOSM", "BNM", "MYNIC")}
    releases = freeze_dosm(f, index, [s.release for s in by_agency["DOSM"]])
    releases += freeze_bnm(f, by_agency["BNM"]) if by_agency["BNM"] else []
    releases += freeze_mynic(f, by_agency["MYNIC"], today) if by_agency["MYNIC"] else []
    return {"taken": today.isoformat(), "catalogue": {"repository": REPO, "commit": commit}, "files": f.files, "releases": releases}


def verify(raw_dir: Path) -> dict[str, Any]:
    """The frozen snapshot, after checking every file against its recorded SHA-256."""
    snapshot = json.loads((raw_dir / SNAPSHOT).read_text("utf-8"))
    for entry in snapshot["files"]:
        path = raw_dir / entry["path"]
        if not path.exists():
            raise ValueError(f"snapshot file {entry['path']} is missing")
        if sha256_of(path) != entry["sha256"]:
            raise ValueError(f"snapshot file {entry['path']} changed: SHA-256 differs from {entry['sha256']}")
    return snapshot


def freeze(raw_dir: Path, statistics: list[Statistic], today: date, get: Get = http_get) -> dict[str, Any]:
    """Take the snapshot unless one exists, then verify it. Only the first call touches the network."""
    if not (raw_dir / SNAPSHOT).exists():
        snapshot = take(raw_dir, statistics, today, get)
        (raw_dir / SNAPSHOT).write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", "utf-8")
    return verify(raw_dir)
