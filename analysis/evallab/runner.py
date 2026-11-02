"""Ask every question of every model in both modes, one call at a time, logging each call so a stopped run resumes."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .ollama import Chat, OllamaError, UsageLimit
from .questions import Question
from .store import Store
from .tools import TOOLS, call_tool

log = logging.getLogger(__name__)

MODES = ("tools", "memory")
MAX_TOOL_CALLS = 6
MAX_TURNS = 10  # chat calls per question at most, so a model that never stops cannot loop forever
RETRIES = 2
BACKOFF_SECONDS = 5.0
SEED = 42
OPTIONS = {"temperature": 0, "seed": SEED}
CAP_NOTE = "Tool call limit reached. Give your final answer now."
ANSWER_FORMAT = ('End your reply with one JSON object and nothing after it: {"value": <number>, "unit": "<unit>", '
                 '"period": "<YYYY-MM for a month or YYYY-Qn for a quarter>", "source": "<dataset id or release URL>"}.')
SYSTEM = {
    "tools": ("You answer questions about Malaysia's official statistics. Today is {today}. Use the tools to find the latest official figure: "
              "datasets on data.gov.my can be out of date, and official releases from DOSM, Bank Negara Malaysia and MYNIC may be newer. " + ANSWER_FORMAT),
    "memory": ("You answer questions about Malaysia's official statistics from what you already know; you have no tools. Today is {today}. "
               "Give the latest official figure you know. " + ANSWER_FORMAT),
}

Sleep = Callable[[float], None]


@dataclass(frozen=True)
class Outcome:
    content: str  # the model's final reply, empty when there was none
    tool_calls: int  # tool calls run, at most MAX_TOOL_CALLS
    seconds: float  # time spent in chat calls, pauses excluded
    status: str  # "ok", "cap" when the tool cap was reached, "error" when a call failed after its retries


class RunLog:
    """Two append-only JSONL files: one line per chat call, one line per finished question run."""

    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.calls_path, self.answers_path = folder / "calls.jsonl", folder / "answers.jsonl"

    @staticmethod
    def _append(path: Path, record: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        records = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines() if path.exists() else [], 1):
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("ignoring unreadable line %d of %s, probably cut short by an interruption", number, path.name)
        return records

    def call(self, record: dict[str, Any]) -> None:
        self._append(self.calls_path, record)

    def answer(self, record: dict[str, Any]) -> None:
        self._append(self.answers_path, record)

    def calls(self) -> list[dict[str, Any]]:
        return self._read(self.calls_path)

    def answers(self) -> list[dict[str, Any]]:
        return self._read(self.answers_path)


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class Asker:
    """One model, one mode, one question at a time, with retries, pacing and a log line per call."""

    def __init__(self, client: Chat, store: Store, run_log: RunLog, today: str, pace: float, sleep: Sleep) -> None:
        self.client, self.store, self.log, self.today, self.pace, self.sleep = client, store, run_log, today, pace, sleep

    def chat(self, model: str, mode: str, question: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> tuple[dict[str, Any], float]:
        for attempt in range(RETRIES + 1):
            start = time.perf_counter()
            record = {"time": now(), "model": model, "mode": mode, "question": question, "attempt": attempt}
            try:
                response = self.client.chat(model, messages, tools, OPTIONS)
            except OllamaError as err:
                seconds = time.perf_counter() - start
                self.log.call({**record, "seconds": round(seconds, 3), "status": "limit" if isinstance(err, UsageLimit) else "error", "error": str(err)[:300]})
                if isinstance(err, UsageLimit) or attempt == RETRIES:
                    raise
                self.sleep(BACKOFF_SECONDS * 2**attempt)
                continue
            seconds = time.perf_counter() - start
            self.log.call({**record, "seconds": round(seconds, 3), "status": "ok",
                           "prompt_tokens": response.get("prompt_eval_count"), "output_tokens": response.get("eval_count")})
            self.sleep(self.pace)
            return response, seconds
        raise AssertionError("unreachable")

    def run_tools(self, calls: list[dict[str, Any]], used: int) -> tuple[list[dict[str, Any]], int]:
        """Tool replies for one assistant message. Calls past the cap are refused, not run."""
        replies = []
        for call in calls:
            name, arguments = call["function"]["name"], call["function"].get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            if used < MAX_TOOL_CALLS:
                content, used = call_tool(self.store, name, arguments), used + 1
            else:
                content = json.dumps({"error": CAP_NOTE})
            replies.append({"role": "tool", "tool_name": name, "content": content})
        return replies, used

    def ask(self, model: str, mode: str, question: Question) -> Outcome:
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM[mode].replace("{today}", self.today)}, {"role": "user", "content": question.text}]
        used, seconds = 0, 0.0
        try:
            for _ in range(MAX_TURNS):
                offer = TOOLS if mode == "tools" and used < MAX_TOOL_CALLS else None
                response, took = self.chat(model, mode, question.id, messages, offer)
                seconds += took
                message = response.get("message", {})
                calls = message.get("tool_calls") or []
                if not calls or offer is None:
                    return Outcome(message.get("content") or "", used, seconds, "cap" if used >= MAX_TOOL_CALLS else "ok")
                replies, used = self.run_tools(calls, used)
                messages = [*messages, message, *replies]
        except UsageLimit:
            raise
        except OllamaError:
            return Outcome("", used, seconds, "error")
        return Outcome("", used, seconds, "cap")


def run(client: Chat, store: Store, questions: list[Question], models: tuple[str, ...], run_log: RunLog, today: str,
        pace: float, only: set[str] | None = None, sleep: Sleep = time.sleep) -> int:
    """Answer every (question, model, mode) not yet in the log. Returns how many were answered now. A usage limit stops the run."""
    done = {(a["question"], a["model"], a["mode"]) for a in run_log.answers()}
    asker = Asker(client, store, run_log, today, pace, sleep)
    answered = 0
    for question in questions:
        if only is not None and question.id not in only:
            continue
        for model in models:
            for mode in MODES:
                if (question.id, model, mode) in done:
                    continue
                outcome = asker.ask(model, mode, question)
                run_log.answer({"time": now(), "question": question.id, "model": model, "mode": mode, **asdict(outcome)})
                answered += 1
                log.info("%s %s %s: %s after %d tool calls", question.id, model, mode, outcome.status, outcome.tool_calls)
    return answered
