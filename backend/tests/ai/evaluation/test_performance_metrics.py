import pytest

from ai.evaluation.latency import (
    evaluate_performance,
    measure_latency,
    measure_throughput,
    time_call,
)


def _counter():
    """A trivial, fast, local callable - no sleeping, no I/O."""
    return 42


def test_time_call_returns_elapsed_seconds_and_result():
    elapsed, result = time_call(_counter)

    assert isinstance(elapsed, float)
    assert elapsed >= 0.0
    assert result == 42


def test_time_call_passes_through_args_and_kwargs():
    def add(a, b, c=0):
        return a + b + c

    elapsed, result = time_call(add, 1, 2, c=3)

    assert result == 6
    assert elapsed >= 0.0


def test_measure_latency_single_invocation():
    stats = measure_latency(_counter, iterations=1)

    assert stats.count == 1
    assert stats.min_seconds == stats.max_seconds == stats.average_seconds
    assert stats.p50_seconds == stats.p95_seconds == stats.p99_seconds
    assert len(stats.samples_seconds) == 1


def test_measure_latency_repeated_invocations_computes_stats():
    stats = measure_latency(_counter, iterations=20)

    assert stats.count == 20
    assert stats.min_seconds <= stats.average_seconds <= stats.max_seconds
    assert stats.total_seconds >= 0.0
    assert len(stats.samples_seconds) == 20


def test_measure_latency_percentiles_are_monotonic():
    stats = measure_latency(_counter, iterations=50)

    assert stats.p50_seconds <= stats.p95_seconds <= stats.p99_seconds


def test_measure_latency_rejects_non_positive_iterations():
    with pytest.raises(ValueError):
        measure_latency(_counter, iterations=0)


def test_measure_latency_with_deterministic_fake_clock(monkeypatch):
    # Force exact, reproducible sample values so percentile math can
    # be checked precisely rather than only "monotonic".
    fake_times = iter([0.0, 1.0, 1.0, 3.0, 3.0, 7.0])
    monkeypatch.setattr(
        "ai.evaluation.latency.time.perf_counter", lambda: next(fake_times),
    )

    stats = measure_latency(_counter, iterations=3)

    assert stats.samples_seconds == (1.0, 2.0, 4.0)
    assert stats.min_seconds == 1.0
    assert stats.max_seconds == 4.0
    assert stats.average_seconds == pytest.approx(7.0 / 3)


def test_measure_throughput_returns_operations_per_second():
    stats = measure_throughput(_counter, iterations=10)

    assert stats.operation_count == 10
    assert stats.elapsed_seconds >= 0.0
    assert stats.operations_per_second > 0.0


def test_measure_throughput_single_operation():
    stats = measure_throughput(_counter, iterations=1)

    assert stats.operation_count == 1


def test_measure_throughput_rejects_non_positive_iterations():
    with pytest.raises(ValueError):
        measure_throughput(_counter, iterations=0)


def test_measure_throughput_handles_zero_elapsed_time(monkeypatch):
    monkeypatch.setattr(
        "ai.evaluation.latency.time.perf_counter", lambda: 0.0,
    )

    stats = measure_throughput(_counter, iterations=5)

    assert stats.elapsed_seconds == 0.0
    assert stats.operations_per_second == float("inf")


def test_evaluate_performance_combines_latency_and_throughput():
    result = evaluate_performance(_counter, iterations=5, label="counter workload")

    assert result.label == "counter workload"
    assert result.latency.count == 5
    assert result.throughput.operation_count == 5
    assert result.throughput.elapsed_seconds >= 0.0


def test_evaluate_performance_passes_through_callable_arguments():
    def add(a, b):
        return a + b

    result = evaluate_performance(add, 3, 1, 2)

    assert result.latency.count == 3


def test_evaluate_performance_rejects_non_positive_iterations():
    with pytest.raises(ValueError):
        evaluate_performance(_counter, iterations=0)
