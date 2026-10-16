"""A tiny synthetic data.gov.my, DOSM, BNM and MYNIC, served from memory, and the snapshot taken from it.

Four real statistics are asked about: the unemployment rate (dataset current), youth unemployment (dataset two months
behind), money supply M3 (BNM, behind) and active .my domains (MYNIC, far behind).
"""

from __future__ import annotations

import io
import json
import tarfile
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl
import pyarrow as pa
import pyarrow.parquet as pq
import pymupdf

from evallab.snapshot import BNM_LISTING, HEAD_URL, MYNIC_URL, TARBALL_URL, freeze
from evallab.statistics import STATISTICS

TODAY = date(2026, 10, 15)
COMMIT = "4ba675a3fc39ee8f1119ef7bc83a588826fe1a65"
STATS = [s for s in STATISTICS if s.id in ("unemployment_rate", "youth_rate_15_24", "m3", "domains_active")]
STORAGE = "https://storage.example/"
EDITION = "https://www.bnm.gov.my/-/monthly-highlights-statistics-in-august-2026-1"
M3_TABLE = "https://www.bnm.gov.my/documents/20124/999/1.3.xlsx"
LFS_TEXT = {  # release period: (unemployment rate, youth rate)
    "2026-08": ("August 2026 eased to 2.9", "10.1"),
    "2026-07": ("July 2026 remained at 3.0", "10.2"),
    "2026-06": ("June 2026 remained at 3.0", "10.2"),
}


def pdf(*pages: str) -> bytes:
    doc = pymupdf.open()
    for text in pages:
        doc.new_page().insert_textbox(pymupdf.Rect(50, 50, 550, 800), text, fontsize=10)
    return doc.tobytes()


def parquet(rows: list[dict[str, Any]]) -> bytes:
    buffer = io.BytesIO()
    pq.write_table(pa.Table.from_pylist(rows), buffer)
    return buffer.getvalue()


def tarball(files: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in files.items():
            data = json.dumps(content).encode()
            info = tarfile.TarInfo(f"datagovmy-meta-{COMMIT}/{name}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def bnm_table() -> bytes:
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append([1.3, None, "Agregat Kewangan: M1, M2 dan M3"])
    sheet.append([None, None, "Monetary Aggregates: M1, M2 and M3"])
    sheet.append(["End of period", None, None, "Total", "Total", "Total"])
    sheet.append([2025, 12, None, 2600000.0, 2590000.0, 730000.0])
    sheet.append([2026, 1, None, 2610000.0, 2600000.0, 731000.0])
    for month, m3 in ((6, 2670359.957), (7, 2659386.335), (8, 2636548.767)):
        sheet.append([None, month, None, m3, m3 - 5000, 740000.0])
    sheet.append([None, "Source: Bank Negara Malaysia"])
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def dataset(id: str, title: str, file: str) -> dict[str, Any]:
    return {"title_en": title, "title_ms": "", "description_en": title, "frequency": "MONTHLY", "data_as_of": "2026-06", "link_parquet": STORAGE + file}


def release(publication: str, day: str) -> dict[str, Any]:
    period = publication[-7:]
    return {
        "publication": publication, "release_date": day,
        "en": {"title": f"[{period}] Labour Force", "description": "Monthly labour force report, covering statistics on unemployment.",
               "resources": [{"resource_type": "excel", "resource_link": f"{STORAGE}lfs_{period}.xlsx"},
                             {"resource_type": "pdf", "resource_link": f"{STORAGE}lfs_{period}_en.pdf"}]},
    }


def catalogue() -> bytes:
    return tarball({
        "data-catalogue/lfs_month.json": dataset("lfs_month", "Monthly Principal Labour Force Statistics", "lfs_month.parquet"),
        "data-catalogue/lfs_month_youth.json": dataset("lfs_month_youth", "Monthly Youth Unemployment", "lfs_month_youth.parquet"),
        "data-catalogue/monetary_aggregates.json": dataset("monetary_aggregates", "Monetary Aggregates", "money_aggregates.parquet"),
        "data-catalogue/domains.json": dataset("domains", "Domain Registrations", "domains.parquet"),
        "data-catalogue/cpi_headline.json": dataset("cpi_headline", "Consumer Price Index", "cpi_2d.parquet"),  # listed, never downloaded
        "data-catalogue/openapi/lfs_month.json": {"not": "a dataset"},
        "pub-dosm/publications/lfs_2026-08.json": release("labour_month_2026-08", "2026-10-09"),
        "pub-dosm/publications/lfs_2026-07.json": release("labour_month_2026-07", "2026-09-11"),
        "pub-dosm/publications/lfs_2026-06.json": release("labour_month_2026-06", "2026-08-11"),
        "pub-dosm/publications/lfs_2026-05.json": release("labour_month_2026-05", "2026-07-10"),  # older than the newest three, never downloaded
    })


def mynic(year: int, totals: dict[int, int]) -> bytes:
    return json.dumps({"year": str(year), "chartData": {str(m): totals.get(m) for m in range(1, 13)}}).encode()


def remote() -> dict[str, bytes]:
    lfs = {f"{STORAGE}lfs_{p}_en.pdf": pdf(f"LABOUR FORCE STATISTICS {p}", f"The unemployment rate for {rate} per cent. The youth unemployment rate for "
                                         f"those aged 15 to 24 years decreased by 0.1 percentage point to {youth} per cent, with 291.3 thousand unemployed persons.")
           for p, (rate, youth) in LFS_TEXT.items()}
    return {
        HEAD_URL: (COMMIT + "\n").encode(),
        TARBALL_URL.format(commit=COMMIT): catalogue(),
        STORAGE + "lfs_month.parquet": parquet([{"date": date(2026, m, 1), "u_rate": r} for m, r in ((6, 3.0), (7, 3.0), (8, 2.9))]),
        STORAGE + "lfs_month_youth.parquet": parquet([{"date": date(2026, m, 1), "u_rate_15_24": 10.2} for m in (5, 6)]),
        STORAGE + "money_aggregates.parquet": parquet([{"date": datetime(2026, 6, 1), "measure": m, "value": v} for m, v in (("m3_total", 2670359.957), ("m1_total", 742082.1))]),
        STORAGE + "domains.parquet": parquet([
            {"series": "cumulative", "date": date(2025, 1, 1), "domain": "overall", "registrations": 352717},
            {"series": "cumulative", "date": date(2025, 1, 1), "domain": ".my", "registrations": 189813},
            {"series": "new_net", "date": date(2025, 1, 1), "domain": "overall", "registrations": 10391},
        ]),
        **lfs,
        BNM_LISTING: f'<a href="https://www.bnm.gov.my/-/monthly-highlights-statistics-in-july-2026">July</a><a href="{EDITION}">Aug</a>'.encode(),
        EDITION: b'<a href="/documents/20124/999/1.3.xlsx">1.3</a><a href="/documents/20124/999/2.1.xlsx">2.1</a>',
        M3_TABLE: bnm_table(),
        MYNIC_URL.format(chart="active", year=2026): mynic(2026, {1: 821903, 8: 826384, 9: 693122}),
        MYNIC_URL.format(chart="active", year=2025): mynic(2025, {1: 352717, 12: 815000}),
    }


def serve(files: dict[str, bytes], asked: list[str] | None = None) -> Callable[[str], bytes]:
    """A stand-in for http_get. Asking for any URL the world does not hold fails the test."""
    def get(url: str) -> bytes:
        if asked is not None:
            asked.append(url)
        return files[url]
    return get


def take_snapshot(raw_dir: Path) -> dict[str, Any]:
    return freeze(raw_dir, STATS, TODAY, serve(remote()))
