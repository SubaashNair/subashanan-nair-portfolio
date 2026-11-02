"""Turn the scored views into the site's LlmEvalResults JSON. All prose comes from templates over computed numbers."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from .questions import OUT_OF_DATE, Question
from .scoring import BASELINE, VIEWS, Cell, Run, rounded
from .statistics import Statistic

DISPLAY = {"gpt-oss:120b-cloud": "gpt-oss 120B", "deepseek-v4.1-flash:cloud": "DeepSeek V4.1 Flash", BASELINE: "Open data only"}
VIEW_LABELS = {"all-tools": "All series, with tools", "stale-tools": "Out-of-date series, with tools", "all-memory": "All series, from memory"}
METRIC = "% with the latest figure"
PER_RULE = 2  # error examples per rule, so at most 6
MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def name(model: str) -> str:
    return DISPLAY.get(model, model)


def pct(value: float) -> int:
    """A share as a whole number, rounding half up like the publications."""
    return int(Decimal(repr(value)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def long_date(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{d.day} {d:%B %Y}"


def period_label(period: str) -> str:
    year, part = period.split("-")
    return f"{part} {year}" if part.startswith("Q") else f"{MONTH_NAMES[int(part) - 1]} {year}"


def figure(value: float, statistic: Statistic) -> str:
    number = f"{rounded(value, statistic.decimals):,}"
    return f"RM{number}{statistic.unit[2:]}" if statistic.unit.startswith("RM ") else f"{number} {statistic.unit}"


def seconds_label(seconds: float) -> str:
    return "under 0.1 s" if seconds < 0.1 else f"{seconds:.1f} s"


def leaders(cells: list[Cell]) -> list[Cell]:
    """The cloud models with the highest rounded share, in model order."""
    clouds = [c for c in cells if c.model != BASELINE]
    top = max(pct(c.share) for c in clouds)
    return [c for c in clouds if pct(c.share) == top]


def answer_text(views: dict[str, list[Cell]]) -> str:
    stale = views["stale-tools"]
    top, base = leaders(stale), next(c for c in stale if c.model == BASELINE)
    against = f"against {pct(base.share)}% for the open data alone."
    if len(top) == 1:
        return f"On out-of-date series, {name(top[0].model)} gave the latest official figure for {pct(top[0].share)}% of questions with tools, {against}"
    return f"On out-of-date series, {join_names([name(c.model) for c in top])} tied, each giving the latest official figure for {pct(top[0].share)}% of questions with tools, {against}"


def key_numbers(views: dict[str, list[Cell]], statistics: int, questions: int, taken: str) -> list[dict[str, str]]:
    top = leaders(views["stale-tools"])
    best = top[0]
    tools = next(c for c in views["all-tools"] if c.model == best.model)
    memory = next(c for c in views["all-memory"] if c.model == best.model)
    gap = pct(tools.share) - pct(memory.share)
    tied = f" Interval for {name(best.model)}." if len(top) > 1 else ""
    change = f"{'higher' if gap > 0 else 'lower'} latest-figure share for {name(best.model)} with tools than from memory" if gap else f"difference for {name(best.model)} between tools and memory"
    return [
        {
            "value": f"{pct(best.share)}%",
            "label": f"of questions on out-of-date series answered with the latest figure by {join_names([name(c.model) for c in top])}, with tools.",
            "caveat": f"95% interval {pct(best.low)} to {pct(best.high)}%, from a bootstrap over statistics.{tied}",
        },
        {
            "value": f"{abs(gap)} point{'' if abs(gap) == 1 else 's'}",
            "label": f"{change}, across all series.",
            "caveat": f"From {pct(memory.share)}% from memory to {pct(tools.share)}% with tools.",
        },
        {
            "value": str(statistics),
            "label": f"statistics, asked 4 ways each: {questions:,} questions verified against the official release.",
            "caveat": f"Snapshot of open data and releases taken on {long_date(taken)}; results describe that day.",
        },
    ]


def row(c: Cell) -> dict[str, Any]:
    score = pct(c.share)
    return {
        "model": name(c.model), "role": "baseline" if c.model == BASELINE else "cloud",
        "score": score, "low": min(pct(c.low), score), "high": max(pct(c.high), score),
        "callsPerAnswer": round(c.calls, 2), "callsLabel": "0" if c.calls == 0 else f"{c.calls:.1f}", "latency": seconds_label(c.seconds),
    }


def tasks(views: dict[str, list[Cell]]) -> list[dict[str, Any]]:
    return [{"id": view, "label": VIEW_LABELS[view], "metric": METRIC, "rows": [row(c) for c in views[view]]} for view, _, _ in VIEWS]


def quoted_dataset(r: Run, s: Statistic) -> bool:
    """The answer gave the out-of-date dataset's figure instead of the release's."""
    q = r.question
    return q.status == OUT_OF_DATE and r.score.value is not None and rounded(r.score.value, s.decimals) == rounded(q.dataset_value, s.decimals)


def failure_note(r: Run, s: Statistic) -> tuple[int, str] | None:
    """The first rule a wrong answer breaks, as (rule number, note); None for a right answer."""
    q = r.question
    if not r.score.readable:
        return 2, "No final JSON answer could be read."
    if r.score.latest:
        return None
    if quoted_dataset(r, s):
        return 0, f"Gave the open dataset's figure for {period_label(q.dataset_period)}, not the release for {period_label(q.period)}."
    if not r.score.period_ok:
        given = period_label(r.score.period) if r.score.period else "no clear period"
        return 1, f"Named {given} instead of {period_label(q.period)}."
    return None


def error_examples(runs: list[Run], statistics: dict[str, Statistic]) -> list[dict[str, Any]]:
    """Up to PER_RULE real failures for each rule, with tools before memory, then by question and model; one example per question."""
    ordered = sorted((r for r in runs if r.model != BASELINE), key=lambda r: (r.mode != "tools", r.question.id, r.model))
    picked: dict[int, list[dict[str, Any]]] = {0: [], 1: [], 2: []}
    used: set[str] = set()
    for r in ordered:
        s = statistics[r.question.statistic]
        found = failure_note(r, s)
        if found is None or r.question.id in used or len(picked[found[0]]) >= PER_RULE:
            continue
        used.add(r.question.id)
        given = "No final answer" if not r.score.readable else ", ".join(
            [figure(r.score.value, s) if r.score.value is not None else "no number", period_label(r.score.period) if r.score.period else "no period"])
        picked[found[0]].append({"input": r.question.text, "expected": f"{figure(r.question.value, s)}, {period_label(r.question.period)}",
                                 "model": f"{name(r.model)}, {'with tools' if r.mode == 'tools' else 'from memory'}", "output": given, "note": found[1], "correct": False})
    return [e for rule in (0, 1, 2) for e in picked[rule]]


def build_results(views: dict[str, list[Cell]], runs: list[Run], questions: list[Question], statistics: dict[str, Statistic],
                  taken: str, run: dict[str, str], retrieved: dict[str, str]) -> dict[str, Any]:
    return {
        "answer": answer_text(views),
        "keyNumbers": key_numbers(views, len({q.statistic for q in questions}), len(questions), taken),
        "run": run,
        "retrieved": retrieved,
        "tasks": tasks(views),
        "errorExamples": error_examples(runs, statistics),
    }


def scores_json(views: dict[str, list[Cell]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Unrounded scores for the manifest, by view and model, with the English and Bahasa Malaysia split."""
    return {
        view: {c.model: {"share": round(c.share, 1), "low": round(c.low, 1), "high": round(c.high, 1), "calls_per_answer": round(c.calls, 2),
                         "median_seconds": round(c.seconds, 2), "questions": c.questions, "source_given": round(c.sourced, 1),
                         "by_language": {k: round(v, 1) for k, v in c.by_language.items()}}
               for c in cells}
        for view, cells in views.items()
    }



