"""Turn the computed shares into the site's PenangResults JSON. All prose comes from templates over computed numbers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np

from .distance import largest_remainder
from .load import CATEGORIES, DISTRICTS

CLINIC, SCHOOL, TRANSIT = range(3)  # category axis, in CATEGORIES order
NEAR, MIDDLE, FAR = range(3)  # band axis: under 1 km, 1 to 3 km, over 3 km
POINTS_NOTE = "To scale. Every public clinic (dental excluded), school and Rapid Penang stop used. Dashed lines mark district boundaries."


@dataclass(frozen=True)
class Findings:
    shares: dict[str, np.ndarray]  # "worldpop" and "meta": percent of residents, shape (districts, categories, bands)
    transit_near: float  # percent of all Penang residents within 1 km of a stop, with WorldPop
    totals: tuple[int, ...]  # DOSM 2020 residents per district
    counts: dict[str, int]  # facilities used per category
    years: tuple[int, int]  # first and last record year of the clinics and schools


def pct(value: int) -> str:
    return "under 1%" if value == 0 else f"{value}%"


def capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def long_date(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{d.day} {d:%B %Y}"


def rounded(shares: np.ndarray) -> np.ndarray:
    """Whole percentages per district and category, each set of three bands summing to exactly 100."""
    return np.array([[largest_remainder(bands) for bands in district] for district in shares], dtype=int)


def worst(shares: np.ndarray) -> int:
    """The district with the largest unrounded share over 3 km from a clinic; the first in DISTRICTS order on a tie."""
    return int(np.argmax(shares[:, CLINIC, FAR]))


def largest_far(r: np.ndarray, category: int) -> str:
    """The largest rounded share over 3 km for a category, and every district that has it."""
    far = r[:, category, FAR]
    names = [DISTRICTS[i].name for i in np.flatnonzero(far == far.max())]
    return f"{pct(int(far.max()))}, in {join_names(names)}"


def answer_text(f: Findings) -> str:
    wp, meta = f.shares["worldpop"], f.shares["meta"]
    r = rounded(wp)
    best, bad = int(np.argmax(wp[:, CLINIC, NEAR])), worst(wp)
    sentences = [
        f"In {DISTRICTS[best].name}, {pct(int(r[best, CLINIC, NEAR]))} of residents live within 1 km of a public clinic by road.",
        f"In {DISTRICTS[bad].name}, {pct(int(r[bad, CLINIC, FAR]))} live more than 3 km away.",
        f"For schools, the largest share more than 3 km away is {largest_far(r, SCHOOL)}; for Rapid Penang stops, it is {largest_far(r, TRANSIT)}.",
    ]
    if worst(meta) != bad:
        sentences.append(f"With Meta's 30 m population map instead of WorldPop, {DISTRICTS[worst(meta)].name} has the largest share more than 3 km from a clinic.")
    return " ".join(sentences)


def key_numbers(f: Findings, gtfs_retrieved: str) -> list[dict[str, str]]:
    bad = worst(f.shares["worldpop"])
    q = int(rounded(f.shares["worldpop"])[bad, CLINIC, FAR])
    q_meta = int(rounded(f.shares["meta"])[bad, CLINIC, FAR])
    first, last = f.years
    return [
        {
            "value": pct(q),
            "label": f"of {DISTRICTS[bad].name} residents live more than 3 km by road from a public clinic.",
            "caveat": capital(f"{pct(q_meta)} with Meta's 30 m population map instead of WorldPop."),
        },
        {
            "value": f"{sum(f.counts.values()):,}",
            "label": "public clinics, schools and Rapid Penang stops mapped.",
            "caveat": f"Dental clinics and private clinics are not included; facility records are dated {first} to {last}.",
        },
        {
            "value": pct(round(f.transit_near)),
            "label": "of Penang residents live within 1 km by road of a Rapid Penang stop.",
            "caveat": f"Stops from the GTFS feed retrieved on {long_date(gtfs_retrieved)}; distance says nothing about how often buses run.",
        },
    ]


def district_entries(f: Findings) -> list[dict[str, Any]]:
    r = rounded(f.shares["worldpop"])
    return [
        {
            "id": d.id,
            "name": d.name,
            "short": d.short,
            "bands": [int(v) for v in r[i, CLINIC]],
            "population": f.totals[i],
            "far": {c: int(r[i, j, FAR]) for j, c in enumerate(CATEGORIES)},
        }
        for i, d in enumerate(DISTRICTS)
    ]


def shares_json(shares: np.ndarray) -> dict[str, dict[str, list[float]]]:
    """Unrounded shares to one decimal place, for the manifest."""
    return {d.id: {c: [round(float(v), 1) for v in shares[i, j]] for j, c in enumerate(CATEGORIES)} for i, d in enumerate(DISTRICTS)}


def build_results(f: Findings, geometry: dict[str, Any], points: list[dict[str, Any]], run: dict[str, str], retrieved: dict[str, str], gtfs_retrieved: str) -> dict[str, Any]:
    return {
        "answer": answer_text(f),
        "keyNumbers": key_numbers(f, gtfs_retrieved),
        "run": run,
        "retrieved": retrieved,
        "districts": district_entries(f),
        "points": points,
        "geometry": geometry,
        "pointsNote": POINTS_NOTE,
    }
