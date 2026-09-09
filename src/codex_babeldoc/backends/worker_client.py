"""Main-process client for the BabelDOC worker subprocess.

Responsibilities:

- write a versioned :class:`WorkerRequest` JSON file
- spawn ``python -m codex_babeldoc.backends.babeldoc_worker <request.json>``
- stream stderr JSONL progress events to a callback
- parse the single stdout JSON document (result or failure)
- enforce a wall-clock timeout and terminate a stuck worker
- map non-zero exit codes to structured :class:`WorkerError` values
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from threading import Event

from codex_babeldoc.backends.worker_protocol import (
    EXIT_COMPLETED,
    EXIT_REQUEST_INVALID,
    PROTOCOL_VERSION,
    TranslatorSpec,
    WorkerError,
    WorkerProgress,
    WorkerRequest,
    WorkerResult,
    request_file_path,
)

logger = logging.getLogger(__name__)

DEFAULT_WORKER_TIMEOUT_SECONDS = 1800.0


class WorkerClientError(Exception):
    """Raised when the worker subprocess cannot produce a valid answer."""

    def __init__(self, error: WorkerError) -> None:
        super().__init__(error.safe_message)
        self.error = error


WORKER_MODE_ARG = "--worker-request"


def worker_command(request_path: Path) -> list[str]:
    """Build the command that starts the BabelDOC worker subprocess.

    A frozen (PyInstaller) ``babelcodex-service`` executable cannot run
    ``python -m codex_babeldoc.backends.babeldoc_worker``, so the packaged
    sidecar dispatches to its own worker subcommand instead. The sidecar entry
    point (:func:`codex_babeldoc.application.sidecar.main`) interprets
    :data:`WORKER_MODE_ARG` and hands control to the worker implementation.
    """
    if getattr(sys, "frozen", False):
        return [sys.executable, WORKER_MODE_ARG, str(request_path)]
    return [
        sys.executable or "python3",
        "-m",
        "codex_babeldoc.backends.babeldoc_worker",
        str(request_path),
    ]


def build_worker_request(request_dict: dict, translator_spec_dict: dict) -> WorkerRequest:
    """Convenience constructor used by the orchestrator."""
    spec = TranslatorSpec(**translator_spec_dict)
    return WorkerRequest(
        request=dict(request_dict),
        translator=spec,
        protocol_version=PROTOCOL_VERSION,
    )


def run_worker(
    request: WorkerRequest,
    working_dir: Path,
    job_id: str,
    on_progress: Callable[[WorkerProgress], None] | None = None,
    timeout_seconds: float = DEFAULT_WORKER_TIMEOUT_SECONDS,
    env_extra: dict[str, str] | None = None,
    cancel_event: Event | None = None,
) -> WorkerResult:
    """Run one translate operation in a fresh worker subprocess."""
    working_dir.mkdir(parents=True, exist_ok=True)
    request_path = request_file_path(working_dir, job_id)
    request_path.write_text(request.to_json(), encoding="utf-8")

    command = worker_command(request_path)
    env = {**os.environ, **(env_extra or {})}

    logger.info("Starting BabelDOC worker for job %s", job_id)
    try:
        proc = subprocess.Popen(
            command,
            cwd=str(working_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except OSError as exc:
        raise WorkerClientError(
            WorkerError(
                category="worker",
                code="WORKER_START_FAILED",
                safe_message="The BabelDOC worker process could not be started.",
                technical_message=str(exc),
            )
        ) from exc

    try:
        return _communicate(proc, on_progress, timeout_seconds, job_id, cancel_event)
    finally:
        if proc.poll() is None:  # pragma: no cover - defensive cleanup
            proc.kill()
            proc.wait(timeout=10)


def _communicate(
    proc: subprocess.Popen[str],
    on_progress: Callable[[WorkerProgress], None] | None,
    timeout_seconds: float,
    job_id: str,
    cancel_event: Event | None = None,
) -> WorkerResult:
    stderr_lines: list[str] = []
    try:
        deadline = time.monotonic() + timeout_seconds
        while True:
            if cancel_event is not None and cancel_event.is_set():
                proc.terminate()
                try:
                    outs, errs = proc.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate(timeout=5)
                _collect_progress(errs, stderr_lines, on_progress)
                raise WorkerClientError(
                    WorkerError(
                        category="cancelled",
                        code="CANCELLED",
                        safe_message="The translation job was cancelled.",
                        technical_message=f"worker terminated for job {job_id}",
                    )
                )
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired("worker", timeout_seconds)
            try:
                outs, errs = proc.communicate(timeout=min(0.25, remaining))
                break
            except subprocess.TimeoutExpired:
                continue
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        proc.communicate()
        raise WorkerClientError(
            WorkerError(
                category="worker",
                code="WORKER_TIMEOUT",
                safe_message=(
                    f"The BabelDOC worker exceeded {timeout_seconds:.0f} seconds "
                    "and was terminated."
                ),
                retryable=True,
                technical_message=str(exc),
            )
        ) from exc

    _collect_progress(errs, stderr_lines, on_progress)

    stdout_text = (outs or "").strip()
    if proc.returncode == EXIT_COMPLETED and stdout_text:
        return _parse_result(stdout_text, job_id)
    raise _failure_from_output(proc.returncode, stdout_text, stderr_lines, job_id)


def _collect_progress(
    stderr_text: str | None,
    stderr_lines: list[str],
    on_progress: Callable[[WorkerProgress], None] | None,
) -> None:
    for line in (stderr_text or "").splitlines():
        stderr_lines.append(line)
        if on_progress is not None:
            progress = _decode_progress_line(line)
            if progress is not None:
                on_progress(progress)


def _decode_progress_line(line: str) -> WorkerProgress | None:
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    if data.get("type") != "progress":
        return None
    return WorkerProgress(
        stage=str(data.get("stage", "unknown")),
        stage_current=data.get("stage_current"),
        stage_total=data.get("stage_total"),
        overall_progress=data.get("overall_progress"),
        message=data.get("message"),
    )


def _parse_result(stdout_text: str, job_id: str) -> WorkerResult:
    try:
        result = WorkerResult.from_json(stdout_text)
    except Exception as exc:
        raise WorkerClientError(
            WorkerError(
                category="worker",
                code="WORKER_PROTOCOL_INVALID",
                safe_message="The BabelDOC worker returned an invalid result.",
                technical_message=str(exc),
            )
        ) from exc
    if result.job_id != job_id:
        raise WorkerClientError(
            WorkerError(
                category="worker",
                code="WORKER_RESULT_MISMATCH",
                safe_message="The BabelDOC worker returned a different job id.",
                technical_message=f"expected {job_id}, got {result.job_id}",
            )
        )
    return result


def _failure_from_output(
    returncode: int,
    stdout_text: str,
    stderr_lines: list[str],
    job_id: str,
) -> WorkerClientError:
    if stdout_text:
        try:
            data = json.loads(stdout_text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict) and data.get("status") == "failed":
            return WorkerClientError(WorkerError.from_json(stdout_text))

    technical = "\n".join(stderr_lines[-30:]) or None
    if returncode == EXIT_REQUEST_INVALID:
        return WorkerClientError(
            WorkerError(
                category="worker",
                code="WORKER_REQUEST_INVALID",
                safe_message="The translation request sent to the worker was invalid.",
                technical_message=technical,
            )
        )
    if not stdout_text:
        return WorkerClientError(
            WorkerError(
                category="worker",
                code="WORKER_CRASHED",
                safe_message="The BabelDOC worker exited without a result.",
                retryable=True,
                technical_message=technical,
            )
        )
    return WorkerClientError(
        WorkerError(
            category="translation",
            code=f"WORKER_EXIT_{returncode}",
            safe_message="The PDF translation failed inside the worker process.",
            retryable=True,
            technical_message=technical,
        )
    )
