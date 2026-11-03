"""A scripted stand-in for the Ollama chat API: each reply is decided by a function of the conversation so far."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

Script = Callable[[str, list[dict[str, Any]], list[dict[str, Any]] | None], dict[str, Any] | Exception]


def tool_call(name: str, **arguments: Any) -> dict[str, Any]:
    return {"function": {"name": name, "arguments": arguments}}


def final(value: Any, unit: str, period: str, source: str, prose: str = "Here is the figure.") -> dict[str, Any]:
    answer = json.dumps({"value": value, "unit": unit, "period": period, "source": source})
    return {"role": "assistant", "content": f"{prose}\n```json\n{answer}\n```"}


class FakeChat:
    def __init__(self, script: Script) -> None:
        self.script, self.requests = script, []

    def chat(self, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, options: dict[str, Any]) -> dict[str, Any]:
        self.requests.append({"model": model, "messages": list(messages), "tools": tools, "options": options})
        reply = self.script(model, messages, tools)
        if isinstance(reply, Exception):
            raise reply
        return {"model": model, "message": reply, "done": True, "prompt_eval_count": 100, "eval_count": 20}
