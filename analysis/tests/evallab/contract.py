"""The rules parseLlmEvalResults (apps/web/src/content/results/parse-llm-eval.ts) enforces, mirrored here so the
pipeline's own tests fail on a file the site would reject."""

from __future__ import annotations

import json
import math
import re
from typing import Any

TASK_IDS = ["all-tools", "stale-tools", "all-memory"]
ROLES = ["cloud", "baseline"]
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def whole(value: Any, low: int, high: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def check_base(r: dict[str, Any]) -> None:
    assert text(r["answer"]), "answer"
    assert len(r["keyNumbers"]) == 3 and all(text(k[f]) for k in r["keyNumbers"] for f in ("value", "label", "caveat")), "keyNumbers"
    assert all(text(r["run"][f]) for f in ("commit", "manifest", "python")) and ISO_DATE.match(r["run"]["lastRun"]), "run"
    assert r["retrieved"] and all(ISO_DATE.match(d) for d in r["retrieved"].values()), "retrieved"


def check_row(path: str, row: dict[str, Any]) -> None:
    assert text(row["model"]) and row["role"] in ROLES, path
    assert all(whole(row[k], 0, 100) for k in ("low", "score", "high")) and row["low"] <= row["score"] <= row["high"], f"{path} score"
    calls = row["callsPerAnswer"]
    assert isinstance(calls, int | float) and not isinstance(calls, bool) and math.isfinite(calls) and 0 <= calls <= 6, f"{path} callsPerAnswer"
    assert text(row["callsLabel"]) and text(row["latency"]), f"{path} labels"


def check_task(i: int, task: dict[str, Any]) -> None:
    assert task["id"] == TASK_IDS[i] and text(task["label"]) and text(task["metric"]), f"tasks[{i}]"
    for j, row in enumerate(task["rows"]):
        check_row(f"tasks[{i}].rows[{j}]", row)
    baselines = sum(r["role"] == "baseline" for r in task["rows"])
    assert baselines == (0 if task["id"] == "all-memory" else 1) and len(task["rows"]) > baselines, f"tasks[{i}] roles"
    assert len({r["model"] for r in task["rows"]}) == len(task["rows"]), f"tasks[{i}] models"


def check_results(r: dict[str, Any]) -> None:
    json.dumps(r, allow_nan=False)  # NaN or infinity would not survive JSON
    check_base(r)
    assert len(r["tasks"]) == 3, "tasks"
    for i, task in enumerate(r["tasks"]):
        check_task(i, task)
    assert len(r["errorExamples"]) <= 6, "errorExamples"
    for e in r["errorExamples"]:
        assert all(text(e[f]) for f in ("input", "expected", "model", "output", "note")) and isinstance(e["correct"], bool), "errorExamples fields"