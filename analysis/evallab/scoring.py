"""Read each final answer, score it against the verified answer, and summarise each model in each view with bootstrap intervals."""

from __future__ import annotations

import json
import re
import statistics as stats
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import numpy as np

from .questions import OUT_OF_DATE, Question
from .statistics import Statistic

RESAMPLES = 2000
SEED = 42
INTERVAL = (2.5, 97.5)
BASELINE = "baseline"
VIEWS = (("all-tools", "tools", False), ("stale-tools", "tools", True), ("all-memory", "memory", False))  # id, mode, out-of-date only
SCALE_WORDS = {"thousand": 1e3, "ribu": 1e3, "million": 1e6, "juta": 1e6, "billion": 1e9, "bilion": 1e9, "trillion": 1e12, "trilion": 1e12}
MONTH_NAMES = (
    ("january", "jan", "januari"), ("february", "feb", "februari"), ("march", "mar", "mac"), ("april", "apr"), ("may", "mei"), ("june", "jun"),
    ("july", "jul", "julai"), ("august", "aug", "ogos", "ogo"), ("september", "sep", "sept"), ("october", "oct", "oktober", "okt"),
    ("november", "nov"), ("december", "dec", "disember", "dis"),
)
MONTHS = {name: i + 1 for i, names in enumerate(MONTH_NAMES) for name in names}
QUARTER_WORDS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "pertama": 1, "kedua": 2, "ketiga": 3, "keempat": 4}
NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


@dataclass(frozen=True)
class Score:
    readable: bool  # a final JSON answer with a value and a period was found
    value_ok: bool
    period_ok: bool
    source_ok: bool
    value: float | None  # the answer's value in the statistic's unit
    period: str | None  # the answer's period as YYYY-MM or YYYY-Qn

    @property
    def latest(self) -> bool:
        return self.value_ok and self.period_ok


@dataclass(frozen=True)
class Run:
    question: Question
    model: str
    mode: str
    score: Score
    tool_calls: int
    seconds: float
    content: str


@dataclass(frozen=True)
class Cell:
    """One model in one view."""

    model: str
    share: float  # % of questions answered with the latest figure
    low: float
    high: float
    calls: float  # mean tool calls per answer
    seconds: float  # median seconds per answer
    questions: int
    by_language: dict[str, float]
    sourced: float = 0.0  # % of answers citing a dataset or release in the snapshot


def parse_answer(content: str) -> dict[str, Any] | None:
    """The last JSON object in a reply that has a value and a period, inside a code fence or not."""
    decoder, found = json.JSONDecoder(), None
    for start in (i for i, ch in enumerate(content) if ch == "{"):
        try:
            candidate, _ = decoder.raw_decode(content, start)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and "value" in candidate and "period" in candidate:
            found = candidate
    return found


def scale_of(text: str) -> float:
    words = re.findall(r"[a-z]+", text.lower())
    return next((SCALE_WORDS[w] for w in words if w in SCALE_WORDS), 1.0)


def in_unit(value: Any, unit: Any, statistic: Statistic) -> float | None:
    """The answer's value in the statistic's unit. A scale word in the value ("RM2.64 trillion") wins over the unit field."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        number, scale = float(value), scale_of(str(unit or ""))
    else:
        match = NUMBER.search(str(value))
        if match is None:
            return None
        number = float(match[0].replace(",", ""))
        scale = scale_of(str(value)) if scale_of(str(value)) != 1.0 else scale_of(str(unit or ""))
    return number * scale / scale_of(statistic.unit)


def rounded(value: float, decimals: int) -> Decimal:
    return Decimal(repr(value)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def as_period(text: Any, quarterly: bool) -> str | None:
    """YYYY-MM or YYYY-Qn from the ways models write a period. A month counts as its quarter for a quarterly statistic."""
    t = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    quarter = (re.search(r"(\d{4}) ?-? ?q([1-4])\b", t) or re.search(r"\bq([1-4]) ?-? ?(\d{4})", t) or re.search(r"\b([1-4])q ?(\d{4})", t)
               or re.search(r"\bst([1-4]) ?(\d{4})", t))
    words = re.search(r"(first|second|third|fourth) quarter (?:of )?(\d{4})|suku (?:tahun )?(pertama|kedua|ketiga|keempat),? (\d{4})", t)
    if quarter or words:
        if not quarterly:
            return None
        if words:
            return f"{words[2] or words[4]}-Q{QUARTER_WORDS[words[1] or words[3]]}"
        year, q = (quarter[1], quarter[2]) if len(quarter[1]) == 4 else (quarter[2], quarter[1])
        return f"{year}-Q{q}"
    month = re.search(r"\b(\d{4})[-/](\d{1,2})\b", t) or re.search(r"\b(\d{1,2})/(\d{4})\b", t)
    if month:
        year, m = (month[1], int(month[2])) if len(month[1]) == 4 else (month[2], int(month[1]))
    else:
        named = re.search(r"\b([a-z]+)\.? (\d{4})\b", t)
        if named is None or named[1] not in MONTHS:
            return None
        year, m = named[2], MONTHS[named[1]]
    if not 1 <= m <= 12:
        return None
    return f"{year}-Q{(m - 1) // 3 + 1}" if quarterly else f"{year}-{m:02d}"


def cites(source: Any, known: frozenset[str]) -> bool:
    """True when the source names a dataset id or a URL that is in the snapshot."""
    text = str(source or "").strip()
    return any((k in text) if "/" in k else re.search(rf"(?<![\w.-]){re.escape(k)}(?![\w-])", text) is not None for k in known)


def score_answer(content: str, question: Question, statistic: Statistic, known: frozenset[str]) -> Score:
    answer = parse_answer(content)
    if answer is None:
        return Score(False, False, False, False, None, None)
    value = in_unit(answer.get("value"), answer.get("unit"), statistic)
    period = as_period(answer.get("period"), statistic.quarterly)
    value_ok = value is not None and rounded(value, statistic.decimals) == rounded(question.value, statistic.decimals)
    return Score(True, value_ok, period == question.period, cites(answer.get("source"), known), value, period)


def score_runs(records: list[dict[str, Any]], questions: list[Question], statistics: dict[str, Statistic], known: frozenset[str]) -> list[Run]:
    """Scored runs from answer records: one per (question, model, mode), the first record winning."""
    by_id = {q.id: q for q in questions}
    seen, runs = set(), []
    for r in records:
        key = (r["question"], r["model"], r["mode"])
        if key in seen or r["question"] not in by_id:
            continue
        seen.add(key)
        q = by_id[r["question"]]
        runs.append(Run(q, r["model"], r["mode"], score_answer(r["content"], q, statistics[q.statistic], known), r["tool_calls"], r["seconds"], r["content"]))
    return runs


def bootstrap(results: list[tuple[str, bool]], resamples: int = RESAMPLES, seed: int = SEED) -> tuple[float, float]:
    """A 95% interval for the share right, resampling statistics with all their questions, since a statistic's questions are not independent."""
    groups: dict[str, list[bool]] = {}
    for statistic, right in results:
        groups.setdefault(statistic, []).append(right)
    hits = np.array([sum(v) for v in groups.values()], dtype=float)
    counts = np.array([len(v) for v in groups.values()], dtype=float)
    picks = np.random.default_rng(seed).integers(0, len(groups), size=(resamples, len(groups)))
    low, high = np.percentile(100 * hits[picks].sum(axis=1) / counts[picks].sum(axis=1), INTERVAL)
    return float(low), float(high)


def cell(model: str, runs: list[Run], seed: int) -> Cell:
    results = [(r.question.statistic, r.score.latest) for r in runs]
    low, high = bootstrap(results, seed=seed)
    languages = sorted({r.question.language for r in runs})
    by_language = {lang: 100 * float(np.mean([r.score.latest for r in runs if r.question.language == lang])) for lang in languages}
    share = 100 * float(np.mean([right for _, right in results]))
    calls = float(np.mean([r.tool_calls for r in runs]))
    sourced = 100 * float(np.mean([r.score.source_ok for r in runs]))
    return Cell(model, share, low, high, calls, float(stats.median(r.seconds for r in runs)), len(runs), by_language, sourced)


def views(runs: list[Run], questions: list[Question], models: tuple[str, ...], seed: int = SEED) -> dict[str, list[Cell]]:
    """Each view's cells: the cloud models in order, then the baseline where it has a mode. Every model must have every question."""
    out = {}
    for view, mode, stale_only in VIEWS:
        wanted = {q.id for q in questions if not stale_only or q.status == OUT_OF_DATE}
        cells = []
        for model in (*models, BASELINE) if mode == "tools" else models:
            chosen = [r for r in runs if r.model == model and r.mode == mode and r.question.id in wanted]
            missing = wanted - {r.question.id for r in chosen}
            if missing:
                raise ValueError(f"{model} has no {mode} answer for {len(missing)} questions, such as {min(missing)}; run again to finish")
            cells.append(cell(model, chosen, seed))
        out[view] = cells
    return out
