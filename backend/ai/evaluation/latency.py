"""
System performance evaluation: latency and throughput for arbitrary
callables/workloads.

Not tied to FastAPI, Celery, or any specific endpoint/pipeline - `fn`
is any zero/positional/keyword-argument callable, so the same
utilities time an AI worker's `.process()`, a repository query, an
HTTP client call, or a plain function equally. Uses
`time.perf_counter()` (a monotonic clock, unaffected by system clock
adjustments) for every measurement. Nothing here sleeps or fabricates
timing - every duration comes from actually invoking `fn`.
"""
import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class LatencyStats:
    """
    Latency distribution across `count` invocations of a workload, all
    in seconds. Percentiles use linear interpolation over the sorted
    sample set; with `count == 1`, every statistic (including every
    percentile) equals that single sample.
    """

    count: int
    total_seconds: float
    average_seconds: float
    min_seconds: float
    max_seconds: float
    p50_seconds: float
    p95_seconds: float
    p99_seconds: float
    samples_seconds: tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ThroughputStats:
    """Completed-operations-per-second for a batch of `operation_count` calls."""

    operation_count: int
    elapsed_seconds: float
    operations_per_second: float


@dataclass(frozen=True)
class PerformanceEvaluationResult:
    """Combined latency + throughput outcome of one benchmark run."""

    label: str
    latency: LatencyStats
    throughput: ThroughputStats
    metadata: dict[str, Any] = field(default_factory=dict)


def _percentile(sorted_samples: list[float], p: float) -> float:
    """Linear-interpolation percentile (p in [0, 1]) over pre-sorted samples."""
    if not sorted_samples:
        return 0.0
    if len(sorted_samples) == 1:
        return sorted_samples[0]

    rank = p * (len(sorted_samples) - 1)
    lower_index = math.floor(rank)
    upper_index = math.ceil(rank)

    if lower_index == upper_index:
        return sorted_samples[lower_index]

    lower_value = sorted_samples[lower_index]
    upper_value = sorted_samples[upper_index]
    fraction = rank - lower_index

    return lower_value + (upper_value - lower_value) * fraction


def _latency_stats_from_samples(samples: list[float]) -> LatencyStats:
    sorted_samples = sorted(samples)
    return LatencyStats(
        count=len(samples),
        total_seconds=sum(samples),
        average_seconds=sum(samples) / len(samples),
        min_seconds=sorted_samples[0],
        max_seconds=sorted_samples[-1],
        p50_seconds=_percentile(sorted_samples, 0.50),
        p95_seconds=_percentile(sorted_samples, 0.95),
        p99_seconds=_percentile(sorted_samples, 0.99),
        samples_seconds=tuple(samples),
    )


def time_call(fn: Callable[..., Any], *args, **kwargs) -> tuple[float, Any]:
    """Invoke `fn(*args, **kwargs)` once; return (elapsed_seconds, fn's return value)."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed, result


def measure_latency(
    fn: Callable[..., Any],
    iterations: int = 1,
    *fn_args,
    **fn_kwargs,
) -> LatencyStats:
    """
    Invoke `fn(*fn_args, **fn_kwargs)` `iterations` times (sequentially)
    and return latency statistics over the per-call elapsed times.
    """
    if iterations <= 0:
        raise ValueError("iterations must be >= 1.")

    samples = [
        time_call(fn, *fn_args, **fn_kwargs)[0]
        for _ in range(iterations)
    ]

    return _latency_stats_from_samples(samples)


def measure_throughput(
    fn: Callable[..., Any],
    iterations: int = 1,
    *fn_args,
    **fn_kwargs,
) -> ThroughputStats:
    """
    Invoke `fn(*fn_args, **fn_kwargs)` `iterations` times back-to-back
    and return operations/second across the whole batch - elapsed time
    is measured once around the entire loop (not summed per-call), so
    this reflects real wall-clock throughput.
    """
    if iterations <= 0:
        raise ValueError("iterations must be >= 1.")

    start = time.perf_counter()
    for _ in range(iterations):
        fn(*fn_args, **fn_kwargs)
    elapsed = time.perf_counter() - start

    operations_per_second = (
        iterations / elapsed if elapsed > 0 else float("inf")
    )

    return ThroughputStats(
        operation_count=iterations,
        elapsed_seconds=elapsed,
        operations_per_second=operations_per_second,
    )


def evaluate_performance(
    fn: Callable[..., Any],
    iterations: int = 1,
    *fn_args,
    label: str = "workload",
    **fn_kwargs,
) -> PerformanceEvaluationResult:
    """
    Run `fn` `iterations` times ONCE (not twice), deriving both
    per-call latency statistics and overall batch throughput from the
    same set of timed invocations.
    """
    if iterations <= 0:
        raise ValueError("iterations must be >= 1.")

    samples: list[float] = []
    batch_start = time.perf_counter()

    for _ in range(iterations):
        elapsed, _ = time_call(fn, *fn_args, **fn_kwargs)
        samples.append(elapsed)

    batch_elapsed = time.perf_counter() - batch_start

    latency = _latency_stats_from_samples(samples)

    throughput = ThroughputStats(
        operation_count=iterations,
        elapsed_seconds=batch_elapsed,
        operations_per_second=(
            iterations / batch_elapsed if batch_elapsed > 0 else float("inf")
        ),
    )

    return PerformanceEvaluationResult(
        label=label, latency=latency, throughput=throughput,
    )
