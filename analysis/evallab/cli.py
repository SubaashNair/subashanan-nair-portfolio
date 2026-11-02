"""Entry point, run from analysis/:

  uv run python -m evallab.cli snapshot      take the snapshot once; later commands only verify it
  uv run python -m evallab.cli draft         draft every answer into evallab/questions.csv for review
  uv run python -m evallab.cli run --pilot   ask the 20 pilot questions and print usage and timing
  uv run python -m evallab.cli run           ask everything not yet answered and print usage and timing
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .ollama import OllamaClient, OllamaError, UsageLimit
from .questions import OUT_OF_DATE, QUESTIONS_PATH, Question, draft_all, read_questions, sheet_rows, write_sheet
from .runner import RunLog, run
from .snapshot import freeze
from .statistics import STATISTICS
from .store import load
from .tools import baseline_answer

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ANALYSIS_DIR.parent
RAW_DIR = ANALYSIS_DIR / "data/raw/evallab"
MODELS = ("gpt-oss:120b-cloud", "deepseek-v4.1-flash:cloud")
PILOT = 20
BY_ID = {s.id: s for s in STATISTICS}


def pilot_ids(questions: list[Question]) -> set[str]:
    """PILOT questions spread evenly over the set, so the pilot touches most statistics and both languages."""
    step = max(1, len(questions) // PILOT)
    return {q.id for q in questions[::step][:PILOT]}


def usage(calls: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, int]]]:
    """Calls, failed calls and tokens per model and mode, from the call log."""
    out: dict[str, dict[str, dict[str, int]]] = {}
    for c in calls:
        u = out.setdefault(c["model"], {}).setdefault(c["mode"], {"calls": 0, "errors": 0, "prompt_tokens": 0, "output_tokens": 0})
        u["calls"] += 1
        u["errors"] += c["status"] != "ok"
        u["prompt_tokens"] += c.get("prompt_tokens") or 0
        u["output_tokens"] += c.get("output_tokens") or 0
    return out


def timing(answers: list[dict[str, Any]]) -> dict[str, Any]:
    if not answers:
        return {"answers": 0}
    return {"answers": len(answers), "median_seconds": round(statistics.median(a["seconds"] for a in answers), 1),
            "tool_calls": sum(a["tool_calls"] for a in answers), "statuses": dict(Counter(a["status"] for a in answers))}


def pilot_summary(answers: list[dict[str, Any]], calls: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Usage from the call log beside timing and outcomes from the answers, per model and mode."""
    return {model: {mode: {**counts, **timing([a for a in answers if a["model"] == model and a["mode"] == mode])} for mode, counts in modes.items()}
            for model, modes in usage(calls).items()}


def cmd_snapshot(args: argparse.Namespace) -> None:
    snapshot = freeze(args.raw_dir, list(STATISTICS), datetime.now(UTC).date())
    print(f"snapshot of {snapshot['taken']}: {len(snapshot['files'])} files, {len(snapshot['releases'])} releases, catalogue at {snapshot['catalogue']['commit'][:8]}")


def cmd_draft(args: argparse.Namespace) -> None:
    drafts = draft_all(load(args.raw_dir), list(STATISTICS))
    write_sheet(args.questions, sheet_rows(drafts), force=args.force)
    stale, blank = sum(d.status == OUT_OF_DATE for d in drafts), [d.statistic.id for d in drafts if d.value is None]
    print(f"wrote {len(drafts) * 4} questions on {len(drafts)} statistics ({stale} out of date) to {args.questions}")
    if blank:
        print(f"no value found in the release text for: {', '.join(blank)}; fill these in by hand")


def cmd_run(args: argparse.Namespace) -> None:
    store = load(args.raw_dir)
    questions = read_questions(args.questions, list(STATISTICS))
    for statistic in {BY_ID[q.statistic] for q in questions}:
        baseline_answer(store, statistic)  # stops now if any statistic has no data in the snapshot
    client = OllamaClient()
    try:
        ollama = {"version": client.version(), "models": {m: client.show(m).get("details", {}) for m in MODELS}}
    except OllamaError as err:
        raise SystemExit(f"Ollama is not reachable at the start of the run: {err}") from err
    logging.info("Ollama %s; models %s", ollama["version"], ollama["models"])
    run_log = RunLog(args.raw_dir / "runs")
    try:
        run(client, store, questions, MODELS, run_log, store.taken, args.pace, only=pilot_ids(questions) if args.pilot else None)
    except UsageLimit as err:
        raise SystemExit(f"stopped at an Ollama Cloud usage limit ({err}); run the same command later to resume") from err
    print(json.dumps(pilot_summary(run_log.answers(), run_log.calls()), indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m evallab.cli", description="Run the LLM Eval Lab freshness study.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot", help="take the snapshot, or verify the one already taken").set_defaults(handler=cmd_snapshot)
    draft = commands.add_parser("draft", help="draft the answers into the review sheet")
    draft.add_argument("--force", action="store_true", help="replace an existing review sheet")
    draft.set_defaults(handler=cmd_draft)
    ask = commands.add_parser("run", help="ask the models every question not yet answered")
    ask.add_argument("--pilot", action="store_true", help=f"ask only {PILOT} questions and print usage")
    ask.add_argument("--pace", type=float, default=2.0, help="seconds to wait after each call")
    ask.set_defaults(handler=cmd_run)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    args.handler(args)


if __name__ == "__main__":
    main()
