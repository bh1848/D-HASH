from unittest.mock import patch

import pytest

from dhash_repro.experiment.modes import resolve_algorithms, run_single_mode

FIXED_METRICS = {
    "throughput_ops_s": 100.0,
    "avg_ms": 1.0,
    "p95_ms": 2.0,
    "p99_ms": 3.0,
    "node_load": {
        "redis-1": 10,
        "redis-2": 10,
        "redis-3": 10,
        "redis-4": 10,
        "redis-5": 10,
    },
}


def test_resolve_algorithms_pipeline_returns_two_expected_modes() -> None:
    assert resolve_algorithms("pipeline", "auto") == ["Consistent Hashing", "D-HASH"]


def test_resolve_algorithms_zipf_returns_all_strategies() -> None:
    assert resolve_algorithms("zipf", "auto") == [
        "Consistent Hashing",
        "Weighted CH",
        "Rendezvous",
        "D-HASH",
    ]


def test_resolve_algorithms_ablation_returns_only_dhash() -> None:
    assert resolve_algorithms("ablation", "auto") == ["D-HASH"]


def test_run_single_mode_consistent_hashing_calls_benchmark_once() -> None:
    with (
        patch(
            "dhash_repro.experiment.modes.flush_databases",
        ) as mock_flush,
        patch(
            "dhash_repro.experiment.modes.preload_cluster",
        ) as mock_preload,
        patch(
            "dhash_repro.experiment.modes.warmup_cluster",
        ) as mock_warmup,
        patch(
            "dhash_repro.experiment.modes.benchmark_cluster",
            return_value=FIXED_METRICS,
        ) as mock_benchmark,
    ):
        result = run_single_mode(["key-a", "key-b"], "Consistent Hashing", 16)

    mock_flush.assert_called_once()
    mock_preload.assert_called_once()
    mock_warmup.assert_called_once()
    mock_benchmark.assert_called_once()
    assert len(result) == 5
    assert all(isinstance(value, float) for value in result)


def test_run_single_mode_dhash_calls_benchmark_once() -> None:
    with (
        patch(
            "dhash_repro.experiment.modes.flush_databases",
        ) as mock_flush,
        patch(
            "dhash_repro.experiment.modes.preload_cluster",
        ) as mock_preload,
        patch(
            "dhash_repro.experiment.modes.warmup_cluster",
        ) as mock_warmup,
        patch(
            "dhash_repro.experiment.modes.benchmark_cluster",
            return_value=FIXED_METRICS,
        ) as mock_benchmark,
    ):
        result = run_single_mode(
            ["key-a", "key-b"],
            "D-HASH",
            32,
            {"T": 100, "W": 32},
        )

    mock_flush.assert_called_once()
    mock_preload.assert_called_once()
    mock_warmup.assert_called_once()
    mock_benchmark.assert_called_once()
    assert len(result) == 5
    assert all(isinstance(value, float) for value in result)


def test_run_single_mode_unknown_mode_raises_value_error() -> None:
    with (
        patch("dhash_repro.experiment.modes.flush_databases"),
        patch("dhash_repro.experiment.modes.preload_cluster"),
        patch("dhash_repro.experiment.modes.warmup_cluster"),
        patch(
            "dhash_repro.experiment.modes.benchmark_cluster",
            return_value=FIXED_METRICS,
        ),
    ):
        with pytest.raises(ValueError):
            run_single_mode(["key-a"], "Unknown", 8)
