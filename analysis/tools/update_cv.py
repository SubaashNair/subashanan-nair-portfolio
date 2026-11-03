"""Rewrites the Forecasting Lab, Penang Pulse and LLM Eval Lab entries on page 2 of the CV from the published results.

Each edit finds the entry in any of its known states (the original wording or an earlier run of this tool), so running it
again on an updated CV is safe.

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
RESULTS_DIR = REPO_DIR / "apps/web/src/content/results"
PAGE = 1  # zero-based: the projects page
RIGHT_EDGE = 562.0  # widest existing body line ends at 561.8
BODY = {"fontname": "helv", "fontsize": 9.5, "color": (0, 0, 0)}  # LiberationSans is metric-compatible with Helvetica
TECH = {"fontname": "heit", "fontsize": 8.5, "color": (0x55 / 255,) * 3}  # Helvetica-Oblique for the grey tech lines
TECH_INSET = 1.5  # the tech line's box overlaps the heading above it by 0.5 pt
LINE_GAP = 15.0  # baselines further apart than this belong to different entries
FORECAST_BULLET = ("Leakage safe 15 minute traffic forecasting",)
PULSE_BULLET = ("Reproducible study of how evenly clinics", "In progress: a reproducible study", "Road distance from every")
FORECAST_TECH_OLD = "Python, scikit-learn, NumPy, SciPy, Pydantic, UCI dataset 608"
FORECAST_TECH_NEW = "Python, scikit-learn, NumPy, SciPy, PyTorch, Chronos, UCI dataset 608"
PULSE_TECH_OLD = (
    "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js, React Three Fiber",
    "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js",
)
PULSE_TECH_NEW = "Python, NumPy, SciPy, NetworkX, rasterio, Shapely, pyosmium, OpenStreetMap, WorldPop, DOSM data, Next.js"
LLM_HEAD = "Tested whether cloud LLMs find Malaysia's latest official figure when open data lags:"
LLM_BULLET = ("Designing a benchmark of a classical baseline", LLM_HEAD)
LLM_TECH_OLD = "Python, LLM APIs, open weight models, bootstrap confidence intervals"
LLM_TECH_NEW = "Python, Ollama Cloud, tool calling, PyMuPDF, bootstrap intervals, data.gov.my, DOSM, BNM, MYNIC"
LLM_LABEL_OLD = "  |  In Progress"
LLM_LABEL_NEW = "  |  LLM Evaluation"
LABEL = {"fontname": "heit", "fontsize": 9.5, "color": (0, 0, 0)}  # the italic label beside an entry's title

Width = Callable[[str], float]


@dataclass(frozen=True)
class Line:
    x: float  # where the text starts, after any bullet
    baseline: float
    top: float
    bottom: float


@dataclass(frozen=True)
class TextLine:
    line: Line
    text: str  # without a leading bullet
    size: float
    bold: bool
    bullet: bool  # starts with a bullet glyph


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


PULSE_LABEL = re.compile(r"^of (?P<district>.+) residents live more than 3 km by road from a public clinic\.$")


def pulse_text(results: dict[str, Any]) -> tuple[str, ...]:
    """Candidate wordings, preferred first, built only from the key numbers in the results file. All start with PULSE_BULLET[-1]."""
    far, count, transit = results["keyNumbers"]
    label = PULSE_LABEL.match(far["label"])
    if label is None:
        raise SystemExit(f"Unexpected Penang Pulse key number label: {far['label']!r}")
    claim = f"{far['value']} of {label['district']} residents live over 3 km from a clinic"
    return (
        f"Road distance from every populated 100 m cell in Penang to the nearest of {count['value']} public clinics, schools and bus stops. "
        f"{claim[0].upper()}{claim[1:]}; {transit['value']} of all residents live within 1 km of a bus stop.",
        f"Road distance from every populated 100 m cell in Penang to the nearest public clinic, school and bus stop; {claim}.",
        f"Road distance from every populated cell in Penang to the nearest clinic, school and bus stop; {claim}.",
    )


LLM_COUNT = re.compile(r"^statistics, asked 4 ways each: (?P<questions>[\d,]+) questions verified")


def llm_text(results: dict[str, Any]) -> tuple[str, ...]:
    """Candidate wordings, preferred first, built only from the results file. All start with LLM_HEAD."""
    stale = next(t for t in results["tasks"] if t["id"] == "stale-tools")["rows"]
    clouds = [r for r in stale if r["role"] == "cloud"]
    best, base = max(clouds, key=lambda r: r["score"]), next(r for r in stale if r["role"] == "baseline")
    count = LLM_COUNT.match(results["keyNumbers"][2]["label"])
    if count is None:
        raise SystemExit(f"Unexpected LLM Eval Lab key number label: {results['keyNumbers'][2]['label']!r}")
    statistics, questions = results["keyNumbers"][2]["value"], count["questions"]
    claim = f"with tools, {best['model']} gave the latest figure on {best['score']}% of out-of-date questions, versus {base['score']}% for the open data alone."
    return (
        f"{LLM_HEAD} {statistics} DOSM, BNM and MYNIC statistics, {questions} verified questions; {claim}",
        f"{LLM_HEAD} {claim}",
        f"{LLM_HEAD} with tools, {best['model']} was right on {best['score']}% of out-of-date questions.",
    )


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


def text_lines(page: Any) -> list[TextLine]:
    """Every text line on the page in reading order, with any leading bullet glyph removed. A bullet on its own is skipped."""
    found = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            chars = [c for span in line["spans"] for c in span["chars"]]
            lead = next((i for i, c in enumerate(chars) if c["c"] not in "• "), len(chars))
            if lead == len(chars):
                continue
            span = line["spans"][0]
            at = Line(x=chars[lead]["bbox"][0], baseline=span["origin"][1], top=line["bbox"][1], bottom=line["bbox"][3])
            text = "".join(c["c"] for c in chars[lead:])
            found.append(TextLine(at, text, round(span["size"], 1), "Bold" in span["font"], chars[0]["c"] == "•"))
    return sorted(found, key=lambda t: (t.line.baseline, t.line.x))


def bullet_lines(page: Any, starts: tuple[str, ...]) -> list[Line]:
    """The line starting with one of `starts`, then its continuation lines: same size, no bullet, not bold, close below."""
    lines = text_lines(page)
    first = next((i for i, t in enumerate(lines) if t.text.startswith(starts)), None)
    if first is None:
        raise SystemExit(f"No line starts with any of {starts}")
    found = [lines[first]]
    for t in lines[first + 1 :]:
        if t.size != found[0].size or t.bold or t.bullet or t.line.baseline - found[-1].line.baseline > LINE_GAP:
            break
        found.append(t)
    return [t.line for t in found]


def replace_bullet(page: Any, starts: tuple[str, ...], candidates: tuple[str, ...], fitz: Any) -> None:
    targets = bullet_lines(page, starts)
    width = lambda s: fitz.get_text_length(s, fontname=BODY["fontname"], fontsize=BODY["fontsize"])  # noqa: E731
    text = choose(candidates, width, [RIGHT_EDGE - line.x for line in targets])
    for line in targets:
        page.add_redact_annot(fitz.Rect(line.x + 0.2, line.top + 0.5, RIGHT_EDGE + 1, line.bottom - 0.5), fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for line, words in zip(targets, text, strict=False):
        page.insert_text((line.x, line.baseline), words, **BODY)


def replace_tech_line(page: Any, old: tuple[str, ...], new: str, fitz: Any, style: dict[str, Any] = TECH) -> None:
    """Swap the one span that reads any of `old`, or `new` from an earlier run, for `new`: a grey tech line unless another style is given."""
    spans = [s for b in page.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"] if s["text"] in (*old, new)]
    if len(spans) != 1:
        raise SystemExit(f"Expected one span reading one of {(*old, new)}, found {len(spans)}")
    span = spans[0]
    end = span["origin"][0] + fitz.get_text_length(new, fontname=style["fontname"], fontsize=style["fontsize"])
    if end > RIGHT_EDGE:
        raise SystemExit(f"{new!r} ends at x = {end:.1f}, past {RIGHT_EDGE}")
    x0, y0, x1, y1 = span["bbox"]
    page.add_redact_annot(fitz.Rect(x0, y0 + TECH_INSET, x1, y1), fill=(1, 1, 1))  # clear of the heading's descenders above
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    page.insert_text(span["origin"], new, **style)


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

    forecast = json.loads((RESULTS_DIR / "forecasting-lab.json").read_text())
    pulse = json.loads((RESULTS_DIR / "penang-pulse.json").read_text())
    llm = json.loads((RESULTS_DIR / "llm-eval-lab.json").read_text())
    doc = fitz.open(args.source)
    render(doc, args.png_dir / f"{args.target.stem}-before.png")
    page = doc[PAGE]
    replace_tech_line(page, PULSE_TECH_OLD, PULSE_TECH_NEW, fitz)
    replace_tech_line(page, (FORECAST_TECH_OLD,), FORECAST_TECH_NEW, fitz)
    replace_bullet(page, PULSE_BULLET, pulse_text(pulse), fitz)
    replace_bullet(page, FORECAST_BULLET, forecast_text(forecast), fitz)
    replace_tech_line(page, (LLM_LABEL_OLD,), LLM_LABEL_NEW, fitz, LABEL)
    replace_tech_line(page, (LLM_TECH_OLD,), LLM_TECH_NEW, fitz)
    replace_bullet(page, LLM_BULLET, llm_text(llm), fitz)
    render(doc, args.png_dir / f"{args.target.stem}-after.png")
    args.target.parent.mkdir(parents=True, exist_ok=True)
    scratch = args.target.with_suffix(".tmp.pdf")
    doc.save(scratch, garbage=3, deflate=True)
    doc.close()
    os.replace(scratch, args.target)
    print(f"wrote {args.target}")


if __name__ == "__main__":
    main()
