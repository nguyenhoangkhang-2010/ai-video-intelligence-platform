from unittest.mock import MagicMock

import pytest

from ai.evaluation.benchmark import BenchmarkRunner
from ai.evaluation.models import EvaluationDataset, MetricResult


def _metric(name, values):
    """A fake Metric that returns `values[i]` on its i-th compute() call."""
    metric = MagicMock()
    metric.name = name
    metric.compute.side_effect = [
        MetricResult(metric_name=name, value=v) for v in values
    ]
    return metric


def _dataset(name="ds", case_count=3):
    return EvaluationDataset(name=name, cases=tuple(object() for _ in range(case_count)))


def test_run_raises_without_at_least_one_metric():
    with pytest.raises(ValueError):
        BenchmarkRunner(metrics=[])


def test_run_returns_zero_valued_results_for_empty_dataset():
    metric = _metric("m1", [])
    runner = BenchmarkRunner(metrics=[metric])
    dataset = EvaluationDataset(name="empty", cases=())

    result = runner.run(dataset)

    assert result.dataset_name == "empty"
    assert result.case_count == 0
    assert len(result.metric_results) == 1
    assert result.metric_results[0].metric_name == "m1"
    assert result.metric_results[0].value == 0.0
    assert result.per_case_results == ()
    metric.compute.assert_not_called()


def test_run_aggregates_metric_values_across_cases_by_mean():
    metric = _metric("precision@5", [1.0, 0.5, 0.0])
    runner = BenchmarkRunner(metrics=[metric])
    dataset = _dataset(case_count=3)

    result = runner.run(dataset)

    assert result.case_count == 3
    assert len(result.metric_results) == 1
    aggregated = result.metric_results[0]
    assert aggregated.metric_name == "precision@5"
    assert aggregated.value == pytest.approx(0.5)
    assert aggregated.details["case_count"] == 3
    assert aggregated.details["scores"] == (1.0, 0.5, 0.0)


def test_run_supports_multiple_metrics_independently():
    metric_a = _metric("a", [1.0, 1.0])
    metric_b = _metric("b", [0.0, 1.0])
    runner = BenchmarkRunner(metrics=[metric_a, metric_b])
    dataset = _dataset(case_count=2)

    result = runner.run(dataset)

    values_by_name = {m.metric_name: m.value for m in result.metric_results}
    assert values_by_name == {"a": 1.0, "b": 0.5}


def test_run_returns_per_case_results_in_case_order():
    metric = _metric("m", [1.0, 0.0])
    runner = BenchmarkRunner(metrics=[metric])
    dataset = _dataset(case_count=2)

    result = runner.run(dataset)

    assert len(result.per_case_results) == 2
    assert result.per_case_results[0][0].value == 1.0
    assert result.per_case_results[1][0].value == 0.0


def test_compare_returns_baseline_treatment_and_delta():
    baseline_metric = _metric("precision@5", [0.5, 0.5])
    runner = BenchmarkRunner(metrics=[baseline_metric])

    baseline_dataset = _dataset(name="baseline", case_count=2)
    treatment_dataset = _dataset(name="treatment", case_count=2)

    # First .run() call (baseline) consumes side_effect[0:2], second
    # (.treatment) consumes side_effect[2:4] - reconfigure to give the
    # treatment run higher scores.
    baseline_metric.compute.side_effect = [
        MetricResult(metric_name="precision@5", value=0.5),
        MetricResult(metric_name="precision@5", value=0.5),
        MetricResult(metric_name="precision@5", value=0.8),
        MetricResult(metric_name="precision@5", value=0.8),
    ]

    comparison = runner.compare(baseline_dataset, treatment_dataset)

    assert comparison["baseline"].metric_results[0].value == pytest.approx(0.5)
    assert comparison["treatment"].metric_results[0].value == pytest.approx(0.8)
    assert comparison["delta"]["precision@5"] == pytest.approx(0.3)
