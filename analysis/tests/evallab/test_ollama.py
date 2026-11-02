import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from evallab.ollama import OllamaClient, OllamaError, UsageLimit

SEEN: list[dict] = []


class FakeOllama(BaseHTTPRequestHandler):
    """Answers like the Ollama server did on 2026-10-15 (version 0.40.4), and with an error for models named after one."""

    def reply(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        self.reply(200, {"version": "0.40.4"})

    def do_POST(self) -> None:  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append({"path": self.path, **body})
        if body["model"] == "limited":
            return self.reply(429, {"error": "you have reached your weekly usage limit"})
        if body["model"] == "broken":
            return self.reply(500, {"error": "internal error"})
        if self.path == "/api/show":
            return self.reply(200, {"capabilities": ["completion", "tools", "thinking"], "details": {"parent_model": "gpt-oss:120b"}})
        message = {"role": "assistant", "content": "", "thinking": "Search first.", "tool_calls": [{"id": "call_1", "function": {"index": 0, "name": "search_datasets", "arguments": {"query": "CPI"}}}]}
        self.reply(200, {"model": "gpt-oss:120b", "message": message, "done": True, "total_duration": 316017665, "prompt_eval_count": 174, "eval_count": 47})

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture(scope="module")
def client() -> Iterator[OllamaClient]:
    server = HTTPServer(("127.0.0.1", 0), FakeOllama)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield OllamaClient(f"http://127.0.0.1:{server.server_port}", timeout=5)
    server.shutdown()


def test_chat_sends_the_messages_tools_and_options(client: OllamaClient) -> None:
    tools = [{"type": "function", "function": {"name": "search_datasets"}}]
    reply = client.chat("gpt-oss:120b-cloud", [{"role": "user", "content": "CPI?"}], tools, {"temperature": 0, "seed": 42})
    assert reply["message"]["tool_calls"][0]["function"]["arguments"] == {"query": "CPI"} and reply["eval_count"] == 47
    assert SEEN[-1] == {"path": "/api/chat", "model": "gpt-oss:120b-cloud", "messages": [{"role": "user", "content": "CPI?"}], "stream": False,
                        "options": {"temperature": 0, "seed": 42}, "tools": tools}
    client.chat("gpt-oss:120b-cloud", [], None, {})
    assert "tools" not in SEEN[-1]


def test_version_and_model_details(client: OllamaClient) -> None:
    assert client.version() == "0.40.4"
    assert client.show("gpt-oss:120b-cloud")["details"]["parent_model"] == "gpt-oss:120b"


def test_a_usage_limit_is_its_own_error(client: OllamaClient) -> None:
    with pytest.raises(UsageLimit, match="HTTP 429 from /api/chat: .*usage limit"):
        client.chat("limited", [], None, {})
    with pytest.raises(OllamaError, match="HTTP 500") as err:
        client.chat("broken", [], None, {})
    assert not isinstance(err.value, UsageLimit)


def test_an_unreachable_server_is_an_ollama_error() -> None:
    with pytest.raises(OllamaError, match="/api/version"):
        OllamaClient("http://127.0.0.1:9", timeout=2).version()
