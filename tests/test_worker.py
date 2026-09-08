"""Tests for the BabelDOC worker process protocol and subprocess client."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from threading import Event
from typing import ClassVar

import pytest

from codex_babeldoc.backends.worker_client import (
    WorkerClientError,
    _communicate,
    build_worker_request,
    run_worker,
)
from codex_babeldoc.backends.worker_protocol import (
    EXIT_REQUEST_INVALID,
    PROTOCOL_VERSION,
    TranslatorSpec,
    WorkerError,
    WorkerRequest,
    WorkerResult,
)
from codex_babeldoc.translators.codex_sdk import build_prime_prompt


class TestProtocolRoundTrip:
    def test_worker_request_json_round_trip(self) -> None:
        request = build_worker_request(
            {
                "job_id": "job-1",
                "source_path": "/tmp/in.pdf",
                "output_dir": "/tmp/out",
                "working_dir": "/tmp/work",
                "lang_in": "en",
                "lang_out": "zh",
            },
            {"name": "mock", "lang_in": "en", "lang_out": "zh"},
        )
        restored = WorkerRequest.from_json(request.to_json())
        assert restored.protocol_version == PROTOCOL_VERSION
        assert restored.request["job_id"] == "job-1"
        assert restored.translator.name == "mock"

    def test_worker_result_json_round_trip(self) -> None:
        result = WorkerResult(
            job_id="job-1",
            artifacts=[],
            total_seconds=1.5,
            backend_name="babeldoc",
            backend_version="0.6.4",
        )
        restored = WorkerResult.from_json(result.to_json())
        assert restored.job_id == "job-1"
        assert restored.backend_version == "0.6.4"

    def test_worker_error_json_round_trip(self) -> None:
        error = WorkerError(
            category="translation",
            code="PLACEHOLDER_MISMATCH",
            safe_message="safe text",
            retryable=True,
            technical_message="detail",
        )
        data = json.loads(error.to_json())
        assert data["status"] == "failed"
        assert data["error"]["code"] == "PLACEHOLDER_MISMATCH"
        restored = WorkerError.from_json(error.to_json())
        assert restored.retryable is True
        assert restored.safe_message == "safe text"

    def test_translator_spec_defaults(self) -> None:
        spec = TranslatorSpec(name="mock", lang_in="en", lang_out="zh")
        assert spec.model is None
        assert spec.effort is None
        assert spec.context_prompt is None
        assert spec.cache_enabled is True
        assert spec.cache_path is None

    def test_translator_spec_context_fields_round_trip(self) -> None:
        spec = TranslatorSpec(
            name="mock",
            lang_in="en",
            lang_out="zh",
            context_prompt="base\n\nterms",
            glossary_prompt="terms",
            glossary_version="g1",
            context_version="c1",
            thread_state_path="/tmp/threads",
            document_id="paper",
        )
        restored = WorkerRequest.from_json(
            WorkerRequest(request={"job_id": "job-1"}, translator=spec).to_json()
        ).translator
        assert restored.context_prompt == "base\n\nterms"
        assert restored.glossary_prompt == "terms"
        assert restored.glossary_version == "g1"
        assert restored.context_version == "c1"
        assert restored.thread_state_path == "/tmp/threads"
        assert restored.document_id == "paper"

    def test_codex_prime_prompt_contains_document_guidance(self) -> None:
        prompt = build_prime_prompt("en", "zh", "Terms: model -> 模型\nTitle: A Paper")
        assert "model -> 模型" in prompt
        assert "Title: A Paper" in prompt
        assert "Reply exactly: READY" in prompt
        assert "markdown fences" in prompt

    def test_codex_sdk_persists_thread_only_after_successful_prime(self, monkeypatch, tmp_path):
        import sys
        import types

        class Result:
            final_response = "READY"

        class FakeThread:
            def __init__(self, thread_id):
                self.id = thread_id
                self.prompts = []

            def run(self, prompt, **kwargs):
                self.prompts.append(prompt)
                return Result()

        class FakeCodex:
            created: ClassVar[list[FakeThread]] = []
            resumed: ClassVar[list[str]] = []

            def thread_start(self, **kwargs):
                thread = FakeThread("thread-new")
                self.created.append(thread)
                return thread

            def thread_resume(self, thread_id, **kwargs):
                self.resumed.append(thread_id)
                return FakeThread(thread_id)

            def close(self):
                pass

        fake_module = types.SimpleNamespace(
            Codex=FakeCodex, Sandbox=types.SimpleNamespace(read_only="read_only")
        )
        monkeypatch.setitem(sys.modules, "openai_codex", fake_module)

        from codex_babeldoc.translation.thread_state import ThreadStateStore
        from codex_babeldoc.translators.codex_sdk import CodexSdkTranslator

        state_root = tmp_path / "threads"
        translator = CodexSdkTranslator(
            "en",
            "zh",
            context_prompt="Title: Paper",
            thread_state_path=str(state_root),
            document_id="paper",
        )
        translator.close()
        assert ThreadStateStore(state_root).load("paper").thread_id == "thread-new"

        translator = CodexSdkTranslator(
            "en",
            "zh",
            thread_state_path=str(state_root),
            document_id="paper",
        )
        translator.close()
        assert FakeCodex.resumed == ["thread-new"]


class TestWorkerEntry:
    def _spawn(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "codex_babeldoc.backends.babeldoc_worker",
                *args,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def test_no_arguments_reports_invalid_request(self, tmp_path: Path) -> None:
        proc = self._spawn()
        assert proc.returncode == EXIT_REQUEST_INVALID
        data = json.loads(proc.stdout.strip())["error"]
        assert data["code"] == "WORKER_REQUEST_INVALID"

    def test_unreadable_request_file_reports_invalid_request(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.json"
        proc = self._spawn(str(missing))
        assert proc.returncode == EXIT_REQUEST_INVALID
        data = json.loads(proc.stdout.strip())["error"]
        assert data["code"] == "WORKER_REQUEST_INVALID"

    def test_worker_stdout_carries_no_ordinary_output(self, tmp_path: Path) -> None:
        """A request whose parse fails must leave stdout protocol-only."""
        proc = self._spawn(str(tmp_path / "nope.json"))
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        assert len(lines) == 1
        json.loads(lines[0])


class TestRunWorker:
    def _request(self, tmp_path: Path) -> WorkerRequest:
        return build_worker_request(
            {
                "job_id": "job-x",
                "source_path": str(tmp_path / "in.pdf"),
                "output_dir": str(tmp_path / "out"),
                "working_dir": str(tmp_path / "work"),
                "lang_in": "en",
                "lang_out": "zh",
            },
            {"name": "mock", "lang_in": "en", "lang_out": "zh"},
        )

    def test_client_maps_invalid_request_error(self, tmp_path: Path) -> None:
        # The source PDF does not exist; if the worker reaches BabelDOC it fails
        # with a translation error, and the client must surface a structured
        # WorkerClientError rather than a raw exception.
        with pytest.raises(WorkerClientError) as excinfo:
            run_worker(
                self._request(tmp_path),
                working_dir=tmp_path / "work",
                job_id="job-x",
                timeout_seconds=120.0,
            )
        assert excinfo.value.error.safe_message
        assert excinfo.value.error.code

    def test_request_file_is_persisted(self, tmp_path: Path) -> None:
        working_dir = tmp_path / "work"
        with pytest.raises(WorkerClientError):
            run_worker(
                self._request(tmp_path),
                working_dir=working_dir,
                job_id="job-x",
                timeout_seconds=120.0,
            )
        files = list(working_dir.glob("*.json"))
        assert files, "worker request file should be written to the working dir"
        payload = json.loads(files[0].read_text(encoding="utf-8"))
        assert payload["request"]["job_id"] == "job-x"
        assert payload["translator"]["name"] == "mock"

    def test_client_terminates_worker_when_cancelled(self) -> None:
        class FakeProcess:
            returncode = -15

            def __init__(self) -> None:
                self.terminated = False
                self.killed = False

            def terminate(self) -> None:
                self.terminated = True

            def kill(self) -> None:
                self.killed = True

            def communicate(self, timeout=None):
                return "", "worker stopped"

            def poll(self):
                return self.returncode

            def wait(self, timeout=None):
                return self.returncode

        process = FakeProcess()
        cancel_event = Event()
        cancel_event.set()
        with pytest.raises(WorkerClientError) as excinfo:
            _communicate(process, None, 10.0, "job-cancel", cancel_event)
        assert process.terminated is True
        assert process.killed is False
        assert excinfo.value.error.category == "cancelled"
        assert excinfo.value.error.code == "CANCELLED"
