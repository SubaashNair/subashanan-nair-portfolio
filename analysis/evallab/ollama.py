"""A small client for the local Ollama server's HTTP API. Cloud models are reached through the same server."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Protocol

DEFAULT_URL = "http://localhost:11434"
TIMEOUT_SECONDS = 300


class OllamaError(Exception):
    """A call that failed: the server answered with an error, timed out or could not be reached."""


class UsageLimit(OllamaError):
    """Ollama Cloud refused the call because a usage limit was reached (HTTP 429). The run stops and resumes later."""


class Chat(Protocol):
    def chat(self, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, options: dict[str, Any]) -> dict[str, Any]: ...


class OllamaClient:
    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = TIMEOUT_SECONDS) -> None:
        self.base_url, self.timeout = base_url.rstrip("/"), timeout

    def _call(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.base_url + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="replace")[:300]
            raise (UsageLimit if err.code == 429 else OllamaError)(f"HTTP {err.code} from {path}: {detail}") from err
        except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
            raise OllamaError(f"{path}: {err}") from err

    def version(self) -> str:
        return str(self._call("/api/version")["version"])

    def show(self, model: str) -> dict[str, Any]:
        return self._call("/api/show", {"model": model})

    def chat(self, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, options: dict[str, Any]) -> dict[str, Any]:
        body: dict[str, Any] = {"model": model, "messages": messages, "stream": False, "options": options}
        if tools:
            body["tools"] = tools
        return self._call("/api/chat", body)
