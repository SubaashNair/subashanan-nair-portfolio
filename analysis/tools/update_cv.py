"""Rewrites the Forecasting Lab and Penang Pulse entries on page 2 of the CV from the published results.

Run from analysis/:
  uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py SOURCE.pdf TARGET.pdf --png-dir DIR
SOURCE and TARGET may be the same file. PyMuPDF is imported inside main(), so the tests need only the standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_DIR = Path(__file__).resolve().parents[2]
RESULTS_PATH = REPO_DIR / "apps/web/src/content/results/forecasting-lab.json"
PAGE = 1  # zero-based: the projects page
RIGHT_EDGE = 562.0  # widest existing body line ends at 561.8
BODY = {"fontname": "helv", "fontsize": 9.5, "color": (0, 0, 0)}  # LiberationSans is metric-compatible with Helvetica
TECH = {"fontname": "heit", "fontsize": 8.5, "color": (0x55 / 255,) * 3}  # Helvetica-Oblique for the grey tech lines
FORECAST_BULLET = "Leakage safe 15 minute traffic forecasting"
PULSE_BULLET = "Reproducible study of how evenly clinics"
FORECAST_TECH_OLD = "Python, scikit-learn, NumPy, SciPy, Pydantic, UCI dataset 608"
FORECAST_TECH_NEW = "Python, scikit-learn, NumPy, SciPy, PyTorch, Chronos, UCI dataset 608"
PULSE_TECH_OLD = "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js, React Three Fiber"
PULSE_TECH_NEW = "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js"
PULSE_TEXT = (
    "In progress: a reproducible study of how far residents in each Penang district live from the nearest public clinic, "
    "school and transit stop, using PeGIS facility layers, 2020 census population and OpenStreetMap roads. "
    "Method, sources and limitations are published ahead of any results.",
    "In progress: a reproducible study of how far residents in each Penang district live from the nearest public clinic, "
    "school and transit stop. Method, sources and limitations are published ahead of any results.",
)

Width = Callable[[str], float]


@dataclass(frozen=True)
class Line:
    x: float  # where the text starts, after any bullet
    baseline: float
    top: float
    bottom: float


def change(name: str, percent: float) -> str:
    return f"{'fell' if percent >= 0 else 'rose'} {round(abs(percent))}% with {name}"


HEADLINE_LABEL = re.compile(r"^lower error than persistence for (?P<name>.+) at \d+ minutes\.$")
HEADLINE_INTERVAL = re.compile(r"95% interval (?P<low>\d+) to (?P<high>\d+)%")
CHRONOS_LABEL = re.compile(r"^lower error for Chronos, with no tuning, than (?P<name>.+) at \d+ hours\.$")


def headline_text(results: dict[str, Any], head: str) -> str | None:
    """The wording with the published interval, parsed from keyNumbers. None unless both changes are reductions."""
    short, long = results["keyNumbers"][0], results["keyNumbers"][1]
    label, chronos_label = HEADLINE_LABEL.match(short["label"]), CHRONOS_LABEL.match(long["label"])
    interval = HEADLINE_INTERVAL.search(short["caveat"])
    if not (label and chronos_label and interval):
        return None
    hours = results["horizons"][-1] // 60
    name, rival = label["name"], chronos_label["name"]
    return (
        f"{head} {name[0].upper()}{name[1:]} cut MAE {short['value']} (95% interval {interval['low']} to {interval['high']}%) "
        f"versus persistence at {results['horizons'][0]} minutes; zero-shot Chronos beat {'it' if rival == name else rival} "
        f"by {long['value']} at {hours} hours."
    )


def forecast_text(results: dict[str, Any]) -> tuple[str, ...]:
    """Candidate wordings, preferred first, built only from numbers in the results file."""
    first = {m["id"]: m["mae"][0] for m in results["models"]}
    cut = {k: 100 * (1 - first[k] / first["persistence"]) for k in ("gb", "mlp", "chronos")}
    minutes = results["horizons"][0]
    sensors = results["keyNumbers"][2]["value"]
    head = f"Leakage safe {minutes} minute traffic forecasting benchmark across a {sensors} sensor network."
    full = (
        f"{head} At {minutes} minutes versus persistence, MAE {change('gradient boosting', cut['gb'])}, "
        f"{change('a spatial MLP', cut['mlp'])} and {change('zero-shot Chronos', cut['chronos'])}."
    )
    short = f"{head} At {minutes} minutes, MAE {change('gradient boosting', cut['gb'])} versus persistence."
    preferred = headline_text(results, head)
    return (full, short) if preferred is None else (preferred, full, short)


def wrap(text: str, width: Width, limits: list[float]) -> list[str] | None:
    """Greedy word wrap into at most len(limits) lines, line i no wider than limits[i]. None when it does not fit."""
    lines: list[str] = []
    for word in text.split():
        if lines and width(f"{lines[-1]} {word}") <= limits[len(lines) - 1]:
            lines[-1] = f"{lines[-1]} {word}"
        elif len(lines) < len(limits) and width(word) <= limits[len(lines)]:
            lines.append(word)
        else:
            return None
    return lines


def choose(candidates: tuple[str, ...], width: Width, limits: list[float]) -> list[str]:
    for text in candidates:
        lines = wrap(text, width, limits)
        if lines is not None:
            return lines
    raise SystemExit(f"No wording fits in {len(limits)} lines; shorten the candidates: {candidates[-1]!r}")


def bullet_lines(page: Any, starts_with: str) -> list[Line]:
    """The bullet line whose text starts with `starts_with`, then its indented continuation lines."""
    lines = [line for block in page.get_text("rawdict")["blocks"] for line in block.get("lines", [])]
    texts = ["".join(c["c"] for span in line["spans"] for c in span["chars"]) for line in lines]
    first = next(i for i, t in enumerate(texts) if t.startswith("•") and t.lstrip("• ").startswith(starts_with))
    found: list[Line] = []
    for line in lines[first:]:
        span = line["spans"][0]
        if found and (span["size"] != lines[first]["spans"][0]["size"] or span["chars"][0]["c"] == "•" or "Bold" in span["font"]):
            break
        chars = [c for s in line["spans"] for c in s["chars"]]
        x = next(c["bbox"][0] for c in chars if c["c"] not in "• ")
        found.append(Line(x=x, baseline=span["origin"][1], top=line["bbox"][1], bottom=line["bbox"][3]))
    return found


def replace_bullet(page: Any, starts_with: str, candidates: tuple[str, ...], fitz: Any) -> None:
    targets = bullet_lines(page, starts_with)
    width = lambda s: fitz.get_text_length(s, fontname=BODY["fontname"], fontsize=BODY["fontsize"])  # noqa: E731
    text = choose(candidates, width, [RIGHT_EDGE - line.x for line in targets])
    for line in targets:
        page.add_redact_annot(fitz.Rect(line.x + 0.2, line.top + 0.5, RIGHT_EDGE + 1, line.bottom - 0.5), fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for line, words in zip(targets, text, strict=False):
        page.insert_text((line.x, line.baseline), words, **BODY)


def replace_tech_line(page: Any, old: str, new: str, fitz: Any) -> None:
    hits = page.search_for(old)
    if len(hits) != 1:
        raise SystemExit(f"Expected one tech line {old!r}, found {len(hits)}")
    span = next(s for b in page.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"] if s["text"] == old)
    end = span["origin"][0] + fitz.get_text_length(new, fontname=TECH["fontname"], fontsize=TECH["fontsize"])
    if end > RIGHT_EDGE:
        raise SystemExit(f"Tech line {new!r} ends at x = {end:.1f}, past {RIGHT_EDGE}")
    page.add_redact_annot(fitz.Rect(span["bbox"]), fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    page.insert_text(span["origin"], new, **TECH)


def render(doc: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc[PAGE].get_pixmap(dpi=110).save(path)


def main(argv: list[str] | None = None) -> None:
    import fitz  # PyMuPDF

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--png-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    results = json.loads(RESULTS_PATH.read_text())
    doc = fitz.open(args.source)
    render(doc, args.png_dir / f"{args.target.stem}-before.png")
    page = doc[PAGE]
    replace_tech_line(page, PULSE_TECH_OLD, PULSE_TECH_NEW, fitz)
    replace_tech_line(page, FORECAST_TECH_OLD, FORECAST_TECH_NEW, fitz)
    replace_bullet(page, PULSE_BULLET, PULSE_TEXT, fitz)
    replace_bullet(page, FORECAST_BULLET, forecast_text(results), fitz)
    render(doc, args.png_dir / f"{args.target.stem}-after.png")
    args.target.parent.mkdir(parents=True, exist_ok=True)
    scratch = args.target.with_suffix(".tmp.pdf")
    doc.save(scratch, garbage=3, deflate=True)
    doc.close()
    os.replace(scratch, args.target)
    print(f"wrote {args.target}")


if __name__ == "__main__":
    main()
