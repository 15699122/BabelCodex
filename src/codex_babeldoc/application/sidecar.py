"""Fixed JSONL sidecar boundary for the future GUI and MCP clients.

The sidecar exposes only scoped job operations. It never accepts a command,
executable, or arbitrary path to remove, and all translation orchestration is
delegated to :class:`BabelCodexService`.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from threading import Lock
from typing import TextIO

from codex_babeldoc.core.errors import BabelCodexError, ErrorCategory, ErrorCode, classify_exception
from codex_babeldoc.core.state import JobState, JobStatus

from .service import BabelCodexService, InvocationSource, StartTranslationCommand

PROTOCOL_VERSION = 1


class SidecarMethod(StrEnum):
    START_TRANSLATION = "start_translation"
    GET_JOB = "get_job"
    LIST_JOBS = "list_jobs"
    CANCEL_JOB = "cancel_job"
    SHUTDOWN = "shutdown"


@dataclass(slots=True)
class _RunningJob:
    job_id: str
    cancel_requested: bool = False
    future: Future[JobState] | None = None


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
        running.future = self._executor.submit(self._run_job, running, source, force)
        return {"job_id": job.job_id, "status": job.status.value}

    def _run_job(self, running: _RunningJob, source: Path, force: bool) -> JobState:
        with self._lock:
            if running.cancel_requested:
                job = self.service.orchestrator.state.load(
                    source,
                    config_fingerprint=self.service.config.fingerprint(),
                )
                job.status = JobStatus.CANCELLED
                self.service.orchestrator.state.save(job)
                return job
        try:
            return self.service.start_translation(
                StartTranslationCommand(
                    source_path=source,
                    force=force,
                    invocation_source=InvocationSource.GUI,
                )
            )
        finally:
            with self._lock:
                self._running.pop(running.job_id, None)

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
        return {"job_id": job_id, "cancelled": True, "status": "cancel_requested"}

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
        if int(request.get("protocol_version", 0)) != PROTOCOL_VERSION:
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
    """Start the sidecar using a fixed config argument."""
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
