"""Tests for the batch worker and response parser."""

from __future__ import annotations

import json
import threading

import pytest

from codex_babeldoc.core.errors import BabelCodexError
from codex_babeldoc.translation.batching import (
    BatchWorker,
    build_batch_payload,
    parse_batch_response,
)
from codex_babeldoc.translation.models import TranslationRequest, TranslationResult


def _req(rid: str, text: str = "hello") -> TranslationRequest:
    return TranslationRequest(
        request_id=rid,
        document_id="doc",
        sequence=0,
        source_text=text,
        source_hash="",
        lang_in="en",
        lang_out="zh",
    )


def test_batch_collects_items_and_flushes():
    received = []

    def handler(batch):
        received.append([p.request.request_id for p in batch])
        return {p.request.request_id: f"translated-{p.request.request_id}" for p in batch}

    worker = BatchWorker(handler, max_items=2, window_ms=10000)
    results = {}

    def submit(rid):
        results[rid] = worker.submit(_req(rid))

    threads = [threading.Thread(target=submit, args=(rid,)) for rid in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    worker.shutdown()

    assert results["a"].translated_text == "translated-a"
    assert results["b"].translated_text == "translated-b"
    assert received == [["a", "b"]]


def test_batch_max_items_triggers_immediate_flush():
    received = []

    def handler(batch):
        received.append(len(batch))
        return {p.request.request_id: "ok" for p in batch}

    worker = BatchWorker(handler, max_items=3, window_ms=10000)
    threads = [threading.Thread(target=worker.submit, args=(_req(f"id-{i}"),)) for i in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    worker.shutdown()

    assert received[0] == 3


def test_batch_missing_id_raises():
    def handler(batch):
        return {}

    worker = BatchWorker(handler, max_items=1, window_ms=10000)
    with pytest.raises(BabelCodexError) as exc_info:
        worker.submit(_req("only"))
    assert exc_info.value.code.value == "BATCH_RESPONSE_MISMATCH"
    worker.shutdown()


def test_batch_shutdown_wakes_pending():
    def handler(batch):
        return {p.request.request_id: "ok" for p in batch}

    worker = BatchWorker(handler, max_items=100, window_ms=100000)
    outcome = []
    thread = threading.Thread(
        target=lambda: _capture_outcome(worker, outcome),
        daemon=True,
    )
    thread.start()
    while not worker._queue:
        pass
    worker.shutdown()
    thread.join(timeout=1)
    assert not thread.is_alive()
    assert outcome
    assert isinstance(outcome[0], (BabelCodexError, TranslationResult))


def test_build_batch_payload_structure():
    worker = BatchWorker(lambda b: {}, max_items=1, window_ms=10000)
    try:
        # Access the private queue by submitting and draining is complex;
        # instead test the helper directly with a synthetic pending list.
        from codex_babeldoc.translation.batching import _PendingRequest

        pending = [_PendingRequest(request=_req("x", "hi"), future=threading.Event())]
        payload = build_batch_payload(pending)
        assert payload["type"] == "translation_batch"
        assert payload["items"][0]["request_id"] == "x"
        assert payload["items"][0]["source_text"] == "hi"
    finally:
        worker.shutdown()


def test_parse_batch_response_valid():
    raw = json.dumps({"a": "译文A", "b": "译文B"})
    result = parse_batch_response(raw, expected_ids={"a", "b"})
    assert result == {"a": "译文A", "b": "译文B"}


def test_parse_batch_response_rejects_mismatch():
    raw = json.dumps({"a": "x"})
    with pytest.raises(BabelCodexError):
        parse_batch_response(raw, expected_ids={"a", "b"})


def test_parse_batch_response_rejects_non_json():
    with pytest.raises(BabelCodexError):
        parse_batch_response("not json", expected_ids={"a"})


def _capture_outcome(worker, outcome):
    try:
        outcome.append(worker.submit(_req("stuck")))
    except Exception as exc:  # noqa: BLE001 - test helper
        outcome.append(exc)
