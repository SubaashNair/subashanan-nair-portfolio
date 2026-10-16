"""Entry point, run from analysis/:

  uv run python -m evallab.cli snapshot      take the snapshot once; later commands only verify it
  uv run python -m evallab.cli draft         draft every answer into evallab/questions.csv for review
"""

from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from .questions import OUT_OF_DATE, QUESTIONS_PATH, draft_all, sheet_rows, write_sheet
from .snapshot import freeze
from .statistics import STATISTICS
from .store import load

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ANALYSIS_DIR.parent
RAW_DIR = ANALYSIS_DIR / "data/raw/evallab"


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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m evallab.cli", description="Run the LLM Eval Lab freshness study.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot", help="take the snapshot, or verify the one already taken").set_defaults(handler=cmd_snapshot)
    draft = commands.add_parser("draft", help="draft the answers into the review sheet")
    draft.add_argument("--force", action="store_true", help="replace an existing review sheet")
    draft.set_defaults(handler=cmd_draft)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    args.handler(args)


if __name__ == "__main__":
    main()
