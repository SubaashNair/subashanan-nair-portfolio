"""Reading each publisher's files once they are on disk: release periods, PDF pages, BNM tables and MYNIC charts. No network."""

from __future__ import annotations

import json
import re
from pathlib import Path

import openpyxl
import pymupdf

MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december")
BNM_EDITION = re.compile(r"https://www\.bnm\.gov\.my/-/monthly-highlights-statistics-in-([a-z]+)-(\d{4})(?:-\d+)?")
BNM_ROWS_IN_TEXT = 24  # months of each table written into the release text


def dosm_period(release_id: str) -> str:
    """The period a DOSM release covers, from its id: labour_month_2026-08 is 2026-08, bop_2026-q2 is 2026-Q2."""
    month = re.search(r"(\d{4})-(\d{2})$", release_id)
    if month:
        return f"{month[1]}-{month[2]}"
    quarter = re.search(r"(\d{4})-q([1-4])$", release_id)
    if quarter:
        return f"{quarter[1]}-Q{quarter[2]}"
    raise ValueError(f"cannot tell the period of release {release_id!r}")


def pdf_pages(path: Path) -> list[str]:
    """The text of every page, with runs of whitespace collapsed to one space."""
    with pymupdf.open(path) as doc:
        return [re.sub(r"\s+", " ", page.get_text()).strip() for page in doc]


def latest_edition(listing_html: str) -> tuple[str, str]:
    """The newest Monthly Highlights and Statistics edition linked from BNM's listing page: its URL and period."""
    editions = {}
    for match in BNM_EDITION.finditer(listing_html):
        month, year = match[1], match[2]
        if month in MONTHS:
            editions[f"{year}-{MONTHS.index(month) + 1:02d}"] = match[0]
    if not editions:
        raise ValueError("no Monthly Highlights and Statistics edition found on the BNM listing page")
    period = max(editions)
    return editions[period], period


def table_link(edition_html: str, table: str) -> str:
    """The XLSX link for one numbered table on an edition page, such as 1.3."""
    match = re.search(rf"/documents/20124/\d+/{re.escape(table)}\.xlsx", edition_html)
    if match is None:
        raise ValueError(f"table {table} not found on the BNM edition page")
    return "https://www.bnm.gov.my" + match[0]


def bnm_rows(path: Path) -> tuple[str, list[tuple[str, tuple[object, ...]]]]:
    """A BNM table's English title and its monthly rows as (YYYY-MM, cells). The year is printed only on January rows."""
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        cells = list(book.worksheets[0].iter_rows(values_only=True))
    finally:
        book.close()
    title = str(cells[1][2]).strip()
    rows, year = [], None
    for row in cells:
        if len(row) > 1 and isinstance(row[1], int) and 1 <= row[1] <= 12:
            year = row[0] if isinstance(row[0], int) else year
            if year is not None:
                rows.append((f"{year}-{row[1]:02d}", row))
    return title, rows


def bnm_latest(path: Path, column: int) -> tuple[float, str] | None:
    """The newest month with a number in this column, as (value, YYYY-MM)."""
    _, rows = bnm_rows(path)
    found = [(float(row[column]), period) for period, row in rows if isinstance(row[column], int | float)]
    return found[-1] if found else None


def bnm_text(path: Path, table: str, columns: dict[int, str]) -> str:
    """The release text for a BNM table: its title and the named columns for the last BNM_ROWS_IN_TEXT months."""
    title, rows = bnm_rows(path)
    lines = [f"Bank Negara Malaysia, Monthly Highlights and Statistics, table {table}: {title}. Source: Bank Negara Malaysia."]
    for period, row in rows[-BNM_ROWS_IN_TEXT:]:
        values = [f"{name} {row[i]:,.4f}" for i, name in sorted(columns.items()) if isinstance(row[i], int | float)]
        lines.append(f"{period}: " + "; ".join(values))
    return "\n".join(lines)


def mynic_points(path: Path) -> list[tuple[str, int]]:
    """Monthly totals from one MYNIC statistics response, as (YYYY-MM, total), months without data left out."""
    data = json.loads(path.read_text("utf-8"))
    year = int(data["year"])
    return [(f"{year}-{int(month):02d}", int(total)) for month, total in sorted(data["chartData"].items(), key=lambda kv: int(kv[0])) if total is not None]


def mynic_text(path: Path, chart: str) -> str:
    lines = [f"MYNIC domain statistics, {chart} domains: monthly totals for all .my domains. Source: MYNIC."]
    lines += [f"{period}: {total:,} domains" for period, total in mynic_points(path)]
    return "\n".join(lines)
