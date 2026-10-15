"""The rules parsePenangResults (apps/web/src/content/results/parse-penang.ts) enforces, mirrored here so the
pipeline's own tests fail on a file the site would reject."""

from __future__ import annotations

import json
import math
import re
from typing import Any

DISTRICT_IDS = ["tl", "bd", "spu", "spt", "sps"]
CATEGORIES = ["clinic", "school", "transit"]
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def whole(value: Any, low: int, high: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def is_path(value: Any) -> bool:
    return text(value) and value.startswith("M")


def check_base(r: dict[str, Any]) -> None:
    assert text(r["answer"]), "answer"
    assert len(r["keyNumbers"]) == 3, "keyNumbers"
    assert all(text(k[f]) for k in r["keyNumbers"] for f in ("value", "label", "caveat")), "keyNumbers fields"
    assert all(text(r["run"][f]) for f in ("commit", "manifest", "python")) and ISO_DATE.match(r["run"]["lastRun"]), "run"
    assert r["retrieved"] and all(ISO_DATE.match(d) for d in r["retrieved"].values()), "retrieved"


def check_district(i: int, d: dict[str, Any]) -> None:
    assert d["id"] == DISTRICT_IDS[i] and text(d["name"]) and text(d["short"]), f"districts[{i}]"
    assert len(d["bands"]) == 3 and all(whole(b, 0, 100) for b in d["bands"]) and sum(d["bands"]) == 100, f"districts[{i}].bands"
    assert whole(d["population"], 1, 2**53 - 1), f"districts[{i}].population"
    assert all(whole(d["far"][c], 0, 100) for c in CATEGORIES) and d["far"]["clinic"] == d["bands"][2], f"districts[{i}].far"


def check_geometry(g: dict[str, Any]) -> None:
    assert is_path(g["island"]) and is_path(g["mainland"]), "geometry outlines"
    assert [d["id"] for d in g["districts"]] == DISTRICT_IDS and all(is_path(d["d"]) and d["land"] in ("island", "mainland") for d in g["districts"]), "geometry.districts"
    assert all(is_path(b) for b in g["boundaries"]), "geometry.boundaries"
    assert len(g["bridges"]) == 2 and all(is_path(b) for b in g["bridges"]), "geometry.bridges"
    assert len(g["places"]) == 6 and all(text(p["text"]) and number(p["x"]) and number(p["y"]) for p in [*g["places"], g["water"]]), "geometry labels"


def check_results(r: dict[str, Any]) -> None:
    json.dumps(r, allow_nan=False)  # NaN or infinity would not survive JSON
    check_base(r)
    assert len(r["districts"]) == 5, "districts"
    for i, d in enumerate(r["districts"]):
        check_district(i, d)
    assert r["points"] and all(p["category"] in CATEGORIES and number(p["x"]) and number(p["y"]) for p in r["points"]), "points"
    check_geometry(r["geometry"])
    assert text(r["pointsNote"]), "pointsNote"
