"""Fixed JSONL sidecar boundary for the future GUI and MCP clients.

The sidecar exposes only scoped job operations. It never accepts a command,
executable, or arbitrary path to remove, and all translation orchestration is
delegated to :class:`BabelCodexService`.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import Event, Lock
from typing import TextIO

from codex_babeldoc.backends.base import ProgressEvent
from codex_babeldoc.backends.worker_client import WORKER_MODE_ARG
from codex_babeldoc.core.errors import BabelCodexError, ErrorCategory, ErrorCode, classify_exception
from codex_babeldoc.core.events import EventType, JobEvent
from codex_babeldoc.core.state import JobState, JobStatus

from .service import BabelCodexService, InvocationSource, StartTranslationCommand

PROTOCOL_VERSION = 1


class SidecarMethod(StrEnum):
    START_TRANSLATION = "start_translation"
    GET_JOB = "get_job"
    LIST_JOBS = "list_jobs"
    CANCEL_JOB = "cancel_job"
    POLL_EVENTS = "poll_events"
    LIST_GLOSSARY = "list_glossary"
    SAVE_GLOSSARY = "save_glossary"
    GET_CONTEXT = "get_context"
    SAVE_CONTEXT = "save_context"
    SHUTDOWN = "shutdown"


@dataclass(slots=True)
class _RunningJob:
    job_id: str
    cancel_requested: bool = False
    future: Future[JobState] | None = None
    cancel_event: Event = field(default_factory=Event)


class SidecarError(ValueError):
    """Raised for malformed or unauthorized sidecar requests."""


def _classify_sidecar_exception(exc: Exception) -> BabelCodexError:
    if isinstance(exc, (SidecarError, json.JSONDecodeError)):
        return BabelCodexError(
            category=ErrorCategory.CONFIG,
            code=ErrorCode.CONFIG_INVALID,
            safe_message=(
                "invalid JSON request" if isinstance(exc, json.JSONDecodeError) else str(exc)
            ),
            retryable=False,
        )
    return classify_exception(exc)


class JsonlSidecar:
    """Dispatch versioned JSONL requests through the shared application service."""

    def __init__(
        self,
        service: BabelCodexService,
        *,
        input_dir: Path | None = None,
        executor: ThreadPoolExecutor | None = None,
    ) -> None:
        self.service = service
        self.input_dir = (input_dir or service.config.project.input_dir).resolve()
        self._executor = executor or ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="babelcodex-sidecar"
        )
        self._owns_executor = executor is None
        self._lock = Lock()
        self._running: dict[str, _RunningJob] = {}
        self._events: list[JobEvent] = []
        self._next_sequence = 1
        self._closed = False

    def handle(self, request: dict[str, object]) -> list[dict[str, object]]:
        """Handle one request and return zero or more protocol messages."""
        request_id = str(request.get("request_id", ""))
        try:
            self._validate_protocol(request)
            method = self._method(request)
            if method is SidecarMethod.START_TRANSLATION:
                result = self._start(request)
            elif method is SidecarMethod.GET_JOB:
                result = self._get_job(request)
            elif method is SidecarMethod.LIST_JOBS:
                result = {"jobs": [job.to_dict() for job in self.service.list_jobs()]}
            elif method is SidecarMethod.CANCEL_JOB:
                result = self._cancel(request)
            elif method is SidecarMethod.POLL_EVENTS:
                result = self._poll_events(request)
            elif method is SidecarMethod.LIST_GLOSSARY:
                result = self._list_glossary(request)
            elif method is SidecarMethod.SAVE_GLOSSARY:
                result = self._save_glossary(request)
            elif method is SidecarMethod.GET_CONTEXT:
                result = self._get_context(request)
            elif method is SidecarMethod.SAVE_CONTEXT:
                result = self._save_context(request)
            elif method is SidecarMethod.SHUTDOWN:
                result = {"closing": True}
                self.close()
            else:  # pragma: no cover - exhaustive enum guard
                raise SidecarError(f"unsupported method: {method}")
            return [{"type": "response", "request_id": request_id, "ok": True, "result": result}]
        except Exception as exc:  # noqa: BLE001 - protocol must not crash on bad input
            error = _classify_sidecar_exception(exc)
            return [
                {
                    "type": "response",
                    "request_id": request_id,
                    "ok": False,
                    "error": {
                        "category": error.category.value,
                        "code": error.code.value,
                        "safe_message": error.safe_message,
                        "retryable": error.retryable,
                    },
                }
            ]

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        if self._owns_executor:
            self._executor.shutdown(wait=False, cancel_futures=True)

    def _start(self, request: dict[str, object]) -> dict[str, object]:
        if self._closed:
            raise SidecarError("sidecar is closed")
        source = self._allowed_source(str(request.get("source_path", "")))
        force = bool(request.get("force", False))
        job = self.service.orchestrator.state.load(
            source,
            config_fingerprint=self.service.config.fingerprint(),
        )
        running = _RunningJob(job_id=job.job_id)
        with self._lock:
            self._running[job.job_id] = running
        self._emit(
            EventType.JOB_CREATED,
            job.job_id,
            {"status": job.status.value, "source_path": job.source_path},
        )
        running.future = self._executor.submit(self._run_job, running, source, force)
        return {"job_id": job.job_id, "status": job.status.value}

    def _run_job(self, running: _RunningJob, source: Path, force: bool) -> JobState:
        with self._lock:
            cancelled_before_start = running.cancel_requested
        if cancelled_before_start:
            job = self.service.orchestrator.state.load(
                source,
                config_fingerprint=self.service.config.fingerprint(),
            )
            job.status = JobStatus.CANCELLED
            self.service.orchestrator.state.save(job)
            self._emit(EventType.STATUS_CHANGED, job.job_id, {"status": job.status.value})
            return job
        try:
            self._emit(
                EventType.STATUS_CHANGED, running.job_id, {"status": JobStatus.RUNNING.value}
            )
            job = self.service.start_translation(
                StartTranslationCommand(
                    source_path=source,
                    force=force,
                    invocation_source=InvocationSource.GUI,
                    on_progress=lambda event: self._on_progress(running.job_id, event),
                    cancel_event=running.cancel_event,
                )
            )
            if job.status is JobStatus.CANCELLED:
                self._emit(EventType.STATUS_CHANGED, running.job_id, {"status": job.status.value})
            else:
                self._emit(
                    EventType.JOB_COMPLETED,
                    running.job_id,
                    {"status": job.status.value, "job": job.to_dict()},
                )
            return job
        except Exception as exc:
            error = _classify_sidecar_exception(exc)
            job = self.service.get_job(running.job_id)
            self._emit(
                EventType.JOB_FAILED,
                running.job_id,
                {
                    "status": job.status.value if job is not None else JobStatus.FAILED.value,
                    "error": {
                        "category": error.category.value,
                        "code": error.code.value,
                        "safe_message": error.safe_message,
                        "retryable": error.retryable,
                    },
                },
            )
            raise
        finally:
            with self._lock:
                self._running.pop(running.job_id, None)

    def _on_progress(self, job_id: str, event: ProgressEvent) -> None:
        self._emit(
            EventType.PROGRESS,
            job_id,
            {
                "stage": event.stage,
                "stage_current": event.stage_current,
                "stage_total": event.stage_total,
                "overall_progress": event.overall_progress,
                "message": event.message,
            },
        )

    def _get_job(self, request: dict[str, object]) -> dict[str, object]:
        job_id = str(request.get("job_id", ""))
        if not job_id:
            raise SidecarError("job_id is required")
        job = self.service.get_job(job_id)
        return {"job": job.to_dict() if job is not None else None}

    def _cancel(self, request: dict[str, object]) -> dict[str, object]:
        job_id = str(request.get("job_id", ""))
        if not job_id:
            raise SidecarError("job_id is required")
        with self._lock:
            running = self._running.get(job_id)
            if running is None:
                job = self.service.get_job(job_id)
                return {
                    "job_id": job_id,
                    "cancelled": False,
                    "status": job.status.value if job else None,
                }
            running.cancel_requested = True
            running.cancel_event.set()
        self._emit(EventType.STATUS_CHANGED, job_id, {"status": "cancel_requested"})
        return {"job_id": job_id, "cancelled": True, "status": "cancel_requested"}

    def _poll_events(self, request: dict[str, object]) -> dict[str, object]:
        raw_after_sequence = request.get("after_sequence", 0)
        if not isinstance(raw_after_sequence, (int, str)):
            raise SidecarError("after_sequence must be an integer")
        try:
            after_sequence = int(raw_after_sequence)
        except (TypeError, ValueError) as exc:
            raise SidecarError("after_sequence must be an integer") from exc
        if after_sequence < 0:
            raise SidecarError("after_sequence must not be negative")
        job_id = str(request.get("job_id", "")) or None
        with self._lock:
            events = [
                self._event_to_dict(event)
                for event in self._events
                if event.sequence > after_sequence and (job_id is None or event.job_id == job_id)
            ]
            next_sequence = self._next_sequence - 1
        return {"events": events, "next_sequence": next_sequence}

    def _list_glossary(self, request: dict[str, object]) -> dict[str, object]:
        scope = str(request.get("scope", "global"))
        document_id = self._optional_document_id(request)
        return self.service.list_glossary(scope=scope, document_id=document_id)

    def _save_glossary(self, request: dict[str, object]) -> dict[str, object]:
        raw_entries = request.get("entries")
        if not isinstance(raw_entries, list) or not all(
            isinstance(entry, dict) for entry in raw_entries
        ):
            raise SidecarError("entries must be a JSON array of objects")
        scope = str(request.get("scope", "global"))
        document_id = self._optional_document_id(request)
        return self.service.save_glossary(
            [dict(entry) for entry in raw_entries], scope=scope, document_id=document_id
        )

    def _get_context(self, request: dict[str, object]) -> dict[str, object]:
        return self.service.get_context(self._required_document_id(request))

    def _save_context(self, request: dict[str, object]) -> dict[str, object]:
        text = request.get("text")
        if not isinstance(text, str):
            raise SidecarError("text must be a string")
        return self.service.save_context(self._required_document_id(request), text)

    @staticmethod
    def _required_document_id(request: dict[str, object]) -> str:
        document_id = str(request.get("document_id", "")).strip()
        if not document_id:
            raise SidecarError("document_id is required")
        if (
            Path(document_id).name != document_id
            or "/" in document_id
            or "\\" in document_id
            or document_id in {".", ".."}
        ):
            raise SidecarError("document_id must be a single document stem")
        return document_id

    @classmethod
    def _optional_document_id(cls, request: dict[str, object]) -> str | None:
        raw = str(request.get("document_id", "")).strip()
        if not raw:
            return None
        if Path(raw).name != raw or "/" in raw or "\\" in raw or raw in {".", ".."}:
            raise SidecarError("document_id must be a single document stem")
        return raw

    def _emit(self, event_type: EventType, job_id: str, payload: dict[str, object]) -> None:
        with self._lock:
            event = JobEvent(
                event_type=event_type,
                job_id=job_id,
                sequence=self._next_sequence,
                timestamp=datetime.now(UTC).isoformat(),
                payload=payload,
            )
            self._next_sequence += 1
            self._events.append(event)

    @staticmethod
    def _event_to_dict(event: JobEvent) -> dict[str, object]:
        return {
            "event_type": event.event_type.value,
            "job_id": event.job_id,
            "sequence": event.sequence,
            "timestamp": event.timestamp,
            "payload": event.payload,
        }

    def _allowed_source(self, raw_path: str) -> Path:
        if not raw_path:
            raise SidecarError("source_path is required")
        source = Path(raw_path).expanduser().resolve()
        try:
            source.relative_to(self.input_dir)
        except ValueError as exc:
            raise SidecarError("source_path is outside the configured input directory") from exc
        if source.suffix.lower() != ".pdf":
            raise SidecarError("source_path must be a PDF")
        if not source.is_file():
            raise FileNotFoundError(source)
        return source

    @staticmethod
    def _validate_protocol(request: dict[str, object]) -> None:
        raw_protocol_version = request.get("protocol_version", 0)
        if not isinstance(raw_protocol_version, (int, str)):
            raise SidecarError("unsupported sidecar protocol version")
        try:
            protocol_version = int(raw_protocol_version)
        except (TypeError, ValueError) as exc:
            raise SidecarError("unsupported sidecar protocol version") from exc
        if protocol_version != PROTOCOL_VERSION:
            raise SidecarError("unsupported sidecar protocol version")
        if not isinstance(request.get("request_id", ""), str):
            raise SidecarError("request_id must be a string")

    @staticmethod
    def _method(request: dict[str, object]) -> SidecarMethod:
        try:
            return SidecarMethod(str(request.get("method", "")))
        except ValueError as exc:
            raise SidecarError("unsupported sidecar method") from exc


def run_jsonl(service: BabelCodexService, stdin: TextIO, stdout: TextIO) -> None:
    """Run the fixed sidecar protocol until EOF or shutdown."""
    sidecar = JsonlSidecar(service)
    try:
        for line in stdin:
            if not line.strip():
                continue
            request: object = {}
            try:
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise SidecarError("request must be a JSON object")
                messages = sidecar.handle(request)
            except Exception as exc:  # noqa: BLE001 - malformed JSON is a protocol response
                error = _classify_sidecar_exception(exc)
                messages = [
                    {
                        "type": "response",
                        "request_id": "",
                        "ok": False,
                        "error": {
                            "category": error.category.value,
                            "code": error.code.value,
                            "safe_message": error.safe_message,
                            "retryable": error.retryable,
                        },
                    }
                ]
            for message in messages:
                stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
                stdout.flush()
            if isinstance(request, dict) and request.get("method") == SidecarMethod.SHUTDOWN.value:
                break
    finally:
        sidecar.close()


def main(argv: list[str] | None = None) -> int:
    """Start the sidecar using a fixed config argument.

    A frozen PyInstaller executable may be spawned by
    :func:`codex_babeldoc.backends.worker_client.worker_command` with the
    worker request flag; in that mode this entry point hands control to the
    BabelDOC worker implementation so a single packaged binary serves both the
    JSONL sidecar and the worker subprocess.
    """
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) >= 2 and argv[0] == WORKER_MODE_ARG:
        from codex_babeldoc.backends.babeldoc_worker import main as worker_main

        return worker_main(argv[1:])

    import argparse

    parser = argparse.ArgumentParser(prog="babelcodex-service")
    parser.add_argument("--config", default="config/example.toml")
    args = parser.parse_args(argv)

    from codex_babeldoc.core.config import load_config

    config = load_config(args.config)
    config.ensure_dirs()
    run_jsonl(BabelCodexService(config), sys.stdin, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
