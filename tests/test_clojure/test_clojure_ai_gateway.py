from __future__ import annotations

import asyncio
import json
import shutil
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional

import pytest

from core.ensemble_project.api.ensemble_project_models import ProjectSelection
from core.settings.clojure_settings import (
    ClojureBridge,
    ClojureProjectGeneratorAIGateway,
    ClojureSettings,
)

pytestmark = pytest.mark.skipif(
    shutil.which("clojure") is None,
    reason="requires the `clojure` CLI + a JVM to build the jpype classpath bridge",
)


@dataclass
class _RecordedRequest:
    path: str
    payload: dict


class _FakeOllamaHandler(BaseHTTPRequestHandler):
    responder: Callable[[dict], dict] = staticmethod(
        lambda payload: {"message": {"content": ""}}
    )
    requests: list = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        payload = json.loads(raw) if raw else {}
        self.__class__.requests.append(_RecordedRequest(self.path, payload))

        response_body = self.__class__.responder(payload)
        encoded = json.dumps(response_body).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):  # noqa: A002 - silence default access logging
        pass


@pytest.fixture(scope="session")
def fake_ollama_server():
    """A tiny threaded HTTP server standing in for a real Ollama daemon."""
    handler_cls = type("FakeOllamaHandler", (_FakeOllamaHandler,), {"requests": []})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    address = server.server_address
    host = address[0]
    port = address[1]
    try:
        yield handler_cls, f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture
def ollama(fake_ollama_server):
    """Reset the responder/requests log before each test."""
    handler_cls, base_url = fake_ollama_server
    handler_cls.requests = []
    handler_cls.responder = staticmethod(lambda payload: {"message": {"content": ""}})

    class Handle:
        base_url_ = base_url

        @staticmethod
        def set_responder(fn: Callable[[dict], dict]) -> None:
            handler_cls.responder = staticmethod(fn)

        @staticmethod
        def last_request() -> Optional[_RecordedRequest]:
            return handler_cls.requests[-1] if handler_cls.requests else None

        @staticmethod
        def request_count() -> int:
            return len(handler_cls.requests)

    return Handle()


def _ollama_content_response(content) -> dict:
    return {"message": {"role": "assistant", "content": content}}


@pytest.fixture(scope="session")
def clojure_bridge(fake_ollama_server):
    _, base_url = fake_ollama_server
    settings = ClojureSettings(OLLAMA_HOST=base_url, OLLAMA_MODEL="test-model")
    return ClojureBridge(settings)


@pytest.fixture(autouse=True)
def _point_bridge_at_fake_server(clojure_bridge, ollama):
    """Make sure the (singleton) bridge is aimed at this test's fake server."""
    clojure_bridge.settings.OLLAMA_HOST = ollama.base_url_
    yield


SAMPLE_PROJECTS = [
    {
        "programming_language": "COBOL",
        "technologies": "React Native",
        "addons": "CI/CD",
        "extras": [],
        "level": 4,
    },
    {
        "programming_language": "Python",
        "technologies": "FastAPI",
        "addons": "PostgreSQL",
        "extras": ["Docker"],
        "level": 3,
    },
]


class TestClojureBridgeChooseValidProject:
    def test_returns_parsed_dict_matching_ollama_response(self, clojure_bridge, ollama):
        ollama.set_responder(
            lambda payload: _ollama_content_response(
                json.dumps({"best_index": 2, "valid": True, "reason": None})
            )
        )

        result = clojure_bridge.choose_valid_project(SAMPLE_PROJECTS)

        assert result == {"best_index": 2, "valid": True, "reason": None}

    def test_invalid_selection_carries_reason_through(self, clojure_bridge, ollama):
        ollama.set_responder(
            lambda payload: _ollama_content_response(
                json.dumps(
                    {
                        "best_index": 1,
                        "valid": False,
                        "reason": "No feasible stack among candidates",
                    }
                )
            )
        )

        result = clojure_bridge.choose_valid_project(SAMPLE_PROJECTS)

        assert result["valid"] is False
        assert result["reason"] == "No feasible stack among candidates"

    def test_sends_model_and_candidate_details_to_ollama(self, clojure_bridge, ollama):
        ollama.set_responder(
            lambda payload: _ollama_content_response(
                json.dumps({"best_index": 1, "valid": True, "reason": None})
            )
        )

        clojure_bridge.choose_valid_project(SAMPLE_PROJECTS)

        sent = ollama.last_request().payload
        assert sent["model"] == "test-model"
        user_message = next(m for m in sent["messages"] if m["role"] == "user")
        # both candidate stacks should show up somewhere in the built prompt
        assert "COBOL" in user_message["content"]
        assert "FastAPI" in user_message["content"]

    def test_raises_when_ollama_returns_no_content(self, clojure_bridge, ollama):
        ollama.set_responder(lambda payload: {"message": {"content": None}})

        with pytest.raises(Exception) as exc_info:
            clojure_bridge.choose_valid_project(SAMPLE_PROJECTS)

        message = str(exc_info.value).lower()
        assert "structured" in message or "projectselection" in message


class TestClojureBridgeGenerateDescription:
    def test_returns_trimmed_plain_text(self, clojure_bridge, ollama):
        ollama.set_responder(
            lambda payload: _ollama_content_response(
                "  Build a REST API with FastAPI and PostgreSQL.  \n"
            )
        )

        result = clojure_bridge.generate_description(SAMPLE_PROJECTS[1])

        assert result == "Build a REST API with FastAPI and PostgreSQL."

    def test_returns_empty_string_when_no_content(self, clojure_bridge, ollama):
        ollama.set_responder(lambda payload: {"message": {"content": None}})

        result = clojure_bridge.generate_description(SAMPLE_PROJECTS[1])

        assert result == ""

    def test_prompt_mentions_project_fields(self, clojure_bridge, ollama):
        ollama.set_responder(lambda payload: _ollama_content_response("A description."))

        clojure_bridge.generate_description(SAMPLE_PROJECTS[1])

        sent = ollama.last_request().payload
        user_message = next(m for m in sent["messages"] if m["role"] == "user")
        assert "FastAPI" in user_message["content"]
        assert "PostgreSQL" in user_message["content"]


@pytest.fixture
def gateway(clojure_bridge):
    gw = ClojureProjectGeneratorAIGateway.__new__(ClojureProjectGeneratorAIGateway)
    gw._bridge = clojure_bridge
    return gw


class TestClojureProjectGeneratorAIGateway:
    def test_choose_valid_project_returns_project_selection(self, gateway, ollama):
        ollama.set_responder(
            lambda payload: _ollama_content_response(
                json.dumps({"best_index": 2, "valid": True, "reason": None})
            )
        )

        selection = asyncio.run(gateway.choose_valid_project(SAMPLE_PROJECTS))

        assert isinstance(selection, ProjectSelection)
        assert selection.best_index == 2
        assert selection.valid is True
        assert selection.reason is None

    def test_generate_description_returns_str(self, gateway, ollama):
        ollama.set_responder(
            lambda payload: _ollama_content_response(
                "Learn FastAPI by building an API."
            )
        )

        description = asyncio.run(gateway.generate_description(SAMPLE_PROJECTS[1]))

        assert description == "Learn FastAPI by building an API."

    def test_choose_valid_project_propagates_gateway_errors(self, gateway, ollama):
        ollama.set_responder(lambda payload: {"message": {"content": None}})

        with pytest.raises(Exception):
            asyncio.run(gateway.choose_valid_project(SAMPLE_PROJECTS))


class TestClojureBridgeSingleton:
    def test_bridge_is_a_singleton_across_instantiations(self, clojure_bridge):
        other = ClojureBridge(
            ClojureSettings(OLLAMA_HOST="http://ignored", OLLAMA_MODEL="ignored")
        )
        assert other is clojure_bridge
        assert other.settings.OLLAMA_HOST == clojure_bridge.settings.OLLAMA_HOST
