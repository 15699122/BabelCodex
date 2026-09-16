"""Deterministic, mock-only benchmark helpers for translation batching."""

from __future__ import annotations

import threading
from dataclasses import asdict

from .batching import BatchWorker
from .models import TranslationRequest


def _request(index: int) -> TranslationRequest:
    return TranslationRequest(
        request_id=f"benchmark-{index}",
        document_id="benchmark",
        sequence=index,
        source_text=f"segment {index}",
        source_hash="",
        lang_in="en",
        lang_out="zh",
    )


def run_benchmark(item_count: int = 24, batch_size: int = 8) -> dict[str, object]:
    """Compare one-turn-per-item with deterministic mock batching."""
    if item_count < 1:
        raise ValueError("item_count must be positive")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    requests = [_request(index) for index in range(item_count)]
    single_results = {
        request.request_id: f"translated {request.source_text}" for request in requests
    }
    turns: list[list[str]] = []

    def handler(batch):
        turns.append([pending.request.request_id for pending in batch])
        return {
            pending.request.request_id: f"translated {pending.request.source_text}"
            for pending in batch
        }

    worker = BatchWorker(handler, max_items=batch_size, window_ms=10)
    try:
        results: dict[str, str] = {}

        def submit(request: TranslationRequest) -> None:
            results[request.request_id] = worker.submit(request).translated_text

        for offset in range(0, len(requests), batch_size):
            group = requests[offset : offset + batch_size]
            barrier = threading.Barrier(len(group))

            def submit_group(
                request: TranslationRequest, *, group_barrier: threading.Barrier = barrier
            ) -> None:
                group_barrier.wait()
                submit(request)

            threads = [threading.Thread(target=submit_group, args=(request,)) for request in group]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        metrics = worker.metrics()
    finally:
        worker.shutdown()

    if results != single_results:
        raise RuntimeError("batch result mismatch against single-turn baseline")

    payload = asdict(metrics)
    payload.update(
        {
            "average_batch_size": metrics.average_batch_size,
            "turn_reduction_ratio": metrics.turn_reduction_ratio,
            "single_turn_baseline": item_count,
            "results_match_baseline": True,
            "network_used": False,
            "real_codex_used": False,
            "turns_detail": len(turns),
        }
    )
    return payload
