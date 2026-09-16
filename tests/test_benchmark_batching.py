"""Tests for the deterministic mock batching benchmark."""

from codex_babeldoc.translation.benchmark import run_benchmark


def test_mock_batch_benchmark_reports_reduction_and_matching_results():
    result = run_benchmark(item_count=10, batch_size=4)

    assert result["submitted_items"] == 10
    assert result["completed_items"] == 10
    assert result["turns"] == 3
    assert result["single_turn_baseline"] == 10
    assert result["max_batch_size"] == 4
    assert result["average_batch_size"] == 10 / 3
    assert result["turn_reduction_ratio"] == 0.7
    assert result["results_match_baseline"] is True
    assert result["network_used"] is False
    assert result["real_codex_used"] is False


def test_mock_batch_benchmark_rejects_invalid_parameters():
    import pytest

    with pytest.raises(ValueError):
        run_benchmark(item_count=0)
    with pytest.raises(ValueError):
        run_benchmark(batch_size=0)
