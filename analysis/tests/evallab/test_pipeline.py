import json
from pathlib import Path

import pytest

from evallab.cli import MODELS, build_manifest, finish
from evallab.questions import Question
from evallab.runner import RunLog
from evallab.store import Store

from .contract import check_results

RUN_INFO = {"commit": "abc1234", "manifest": "analysis/outputs/llm-eval-lab-manifest.json", "python": "3.12.9", "lastRun": "2026-10-16"}


def test_a_full_run_on_the_synthetic_world_passes_the_site_contract(store: Store, questions: list[Question], answered: RunLog) -> None:
    results, scored = finish(store, questions, answered.answers(), RUN_INFO)
    check_results(results)

    shares = {t["id"]: {r["model"]: r["score"] for r in t["rows"]} for t in results["tasks"]}
    assert shares == {
        "all-tools": {"gpt-oss 120B": 100, "DeepSeek V4.1 Flash": 25, "Open data only": 25},
        "stale-tools": {"gpt-oss 120B": 100, "DeepSeek V4.1 Flash": 0, "Open data only": 0},
        "all-memory": {"gpt-oss 120B": 0, "DeepSeek V4.1 Flash": 0},
    }
    assert results["answer"] == "On out-of-date series, gpt-oss 120B gave the latest official figure for 100% of questions with tools, against 0% for the open data alone."
    assert [k["value"] for k in results["keyNumbers"]] == ["100%", "100 points", "4"]
    assert results["retrieved"] == {"data.gov.my datasets": "2026-10-15", "DOSM releases": "2026-10-15", "Bank Negara Malaysia": "2026-10-15",
                                    "MYNIC": "2026-10-15", "Question set": "2026-10-15", "Ollama Cloud": "2026-10-16"}
    assert {e["note"].split(" ")[0] for e in results["errorExamples"]} == {"Gave", "Named", "No"}
    assert scored["stale-tools"]["baseline"]["share"] == 0.0 and scored["all-tools"][MODELS[0]]["by_language"] == {"en": 100.0, "ms": 100.0}
    assert scored["all-tools"][MODELS[0]]["source_given"] == 100.0 and scored["all-memory"][MODELS[0]]["source_given"] == 0.0


def test_the_manifest_records_the_provenance_of_a_run(store: Store, questions: list[Question], answered: RunLog, tmp_path: Path) -> None:
    sheet = tmp_path / "questions.csv"
    sheet.write_text("id\n")
    _, scored = finish(store, questions, answered.answers(), RUN_INFO)
    ollama = {"version": "0.40.4", "models": {m: {"parent_model": m.split(":")[0]} for m in MODELS}}
    manifest = build_manifest(store, questions, sheet, scored, answered, ollama, {"python": "3.12.9"}, {"commit": "abc1234", "dirty": False})

    assert manifest["snapshot"]["taken"] == "2026-10-15" and manifest["snapshot"]["catalogue"]["commit"].startswith("4ba675a3")
    assert manifest["questions"]["questions"] == 16 and manifest["questions"]["out_of_date_statistics"] == ["domains_active", "m3", "youth_rate_15_24"]
    assert manifest["runs"] == {m: {"tools": 16, "memory": 16} for m in MODELS}
    assert manifest["usage"][MODELS[0]]["tools"] == {"calls": 32, "errors": 0, "prompt_tokens": 3200, "output_tokens": 640}
    assert manifest["settings"]["bootstrap"] == {"unit": "statistic", "resamples": 2000, "seed": 42} and manifest["ollama_version"] == "0.40.4"
    assert manifest["results_file"] == "apps/web/src/content/results/llm-eval-lab.json"
    json.dumps(manifest, allow_nan=False)


def test_scoring_stops_while_any_answer_is_missing(store: Store, questions: list[Question], answered: RunLog) -> None:
    with pytest.raises(ValueError, match="has no tools answer"):
        finish(store, questions, answered.answers()[1:], RUN_INFO)