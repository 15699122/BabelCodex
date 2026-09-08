"""Short-window batch queue for translation requests.

BabelDOC invokes the translator synchronously from one or more worker
threads, but Codex turns carry fixed overhead. Rather than issuing one turn
per segment, this module collects requests over a small time window and hands
the whole batch to a single Codex turn, then distributes results back to the
waiting callers by stable request ID.

Only one Codex thread is ever in flight at a time; the batch worker serialises
turns so the per-document thread contract is never violated.
"""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from codex_babeldoc.core.errors import BabelCodexError, ErrorCategory, ErrorCode

from .models import TranslationRequest, TranslationResult

log = logging.getLogger(__name__)


@dataclass(slots=True)
class _PendingRequest:
    request: TranslationRequest
    future: threading.Event
    result: TranslationResult | None = None
    error: Exception | None = None


class BatchWorker:
    """Collects translation requests and flushes them in small batches."""

    def __init__(
        self,
        batch_handler: Callable[[list[_PendingRequest]], dict[str, str]],
        *,
        max_items: int = 8,
        max_chars: int = 12000,
        window_ms: float = 50.0,
        request_timeout_seconds: float = 180.0,
    ) -> None:
        self._handler = batch_handler
        self._max_items = max_items
        self._max_chars = max_chars
        self._window_seconds = window_ms / 1000.0
        self._request_timeout = request_timeout_seconds

        self._lock = threading.Lock()
        self._queue: list[_PendingRequest] = []
        self._flush_event = threading.Event()
        self._shutdown = False
        self._worker = threading.Thread(
            target=self._run,
            name="babelcodex-batch-worker",
            daemon=True,
        )
        self._worker.start()

    def submit(self, request: TranslationRequest) -> TranslationResult:
        """Enqueue a request and block until its result is available."""
        pending = _PendingRequest(request=request, future=threading.Event())
        with self._lock:
            self._queue.append(pending)
            if len(self._queue) >= self._max_items:
                self._flush_event.set()

        if not pending.future.wait(timeout=self._request_timeout):
            raise BabelCodexError(
                category=ErrorCategory.TRANSLATION,
                code=ErrorCode.CODEX_TIMEOUT,
                safe_message="Translation request timed out waiting for batch turn.",
                retryable=True,
            )
        if pending.error is not None:
            raise pending.error
        assert pending.result is not None
        return pending.result

    def shutdown(self, *, timeout: float = 5.0) -> None:
        """Stop the worker and wake every waiting caller with an error."""
        self._shutdown = True
        self._flush_event.set()
        self._worker.join(timeout=timeout)
        with self._lock:
            remaining = self._queue
            self._queue = []
        for pending in remaining:
            pending.error = BabelCodexError(
                category=ErrorCategory.TRANSLATION,
                code=ErrorCode.CODEX_TIMEOUT,
                safe_message="Translation gateway is shutting down.",
                retryable=True,
            )
            pending.future.set()

    # ------------------------------------------------------------------
    def _run(self) -> None:
        while not self._shutdown:
            self._flush_event.wait(timeout=self._window_seconds)
            self._flush_event.clear()
            batch = self._drain()
            if batch:
                self._flush(batch)

    def _drain(self) -> list[_PendingRequest]:
        with self._lock:
            if not self._queue:
                return []
            batch: list[_PendingRequest] = []
            chars = 0
            while self._queue and len(batch) < self._max_items:
                candidate = self._queue[0]
                size = len(candidate.request.source_text)
                if batch and chars + size > self._max_chars:
                    break
                self._queue.pop(0)
                batch.append(candidate)
                chars += size
        return batch

    def _flush(self, batch: list[_PendingRequest]) -> None:
        try:
            results = self._handler(batch)
        except Exception as exc:  # noqa: BLE001 - surface to every waiter
            for pending in batch:
                pending.error = exc
                pending.future.set()
            return

        for pending in batch:
            rid = pending.request.request_id
            if rid in results:
                pending.result = TranslationResult(
                    request_id=rid,
                    translated_text=results[rid],
                    validation_status="pending",
                )
            else:
                pending.error = BabelCodexError(
                    category=ErrorCategory.TRANSLATION,
                    code=ErrorCode.BATCH_RESPONSE_MISMATCH,
                    safe_message=f"Codex batch response did not include request {rid}.",
                    retryable=True,
                )
            pending.future.set()


def build_batch_payload(batch: list[_PendingRequest]) -> dict[str, Any]:
    """Build the structured payload sent to Codex for a batch turn."""
    return {
        "type": "translation_batch",
        "items": [
            {
                "request_id": p.request.request_id,
                "source_text": p.request.source_text,
                "source_language": p.request.lang_in,
                "target_language": p.request.lang_out,
            }
            for p in batch
        ],
    }


def parse_batch_response(
    raw: str,
    *,
    expected_ids: set[str],
) -> dict[str, str]:
    """Parse a Codex batch response and validate the request-ID set."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BabelCodexError(
            category=ErrorCategory.TRANSLATION,
            code=ErrorCode.BATCH_RESPONSE_MISMATCH,
            safe_message="Codex batch response was not valid JSON.",
            retryable=True,
            technical_message=str(exc),
        ) from exc

    if not isinstance(data, dict):
        raise BabelCodexError(
            category=ErrorCategory.TRANSLATION,
            code=ErrorCode.BATCH_RESPONSE_MISMATCH,
            safe_message="Codex batch response was not a JSON object.",
            retryable=True,
        )

    returned = set(data.keys())
    if returned != expected_ids:
        missing = expected_ids - returned
        extra = returned - expected_ids
        raise BabelCodexError(
            category=ErrorCategory.TRANSLATION,
            code=ErrorCode.BATCH_RESPONSE_MISMATCH,
            safe_message=(
                "Codex batch response ID set did not match request set "
                f"(missing={len(missing)}, extra={len(extra)})."
            ),
            retryable=True,
        )

    return {key: str(value) for key, value in data.items()}
