"""
Generic benchmark runner: an EvaluationDataset + one or more Metrics
in, a structured BenchmarkResult out.

Adding a new metric never requires touching BenchmarkRunner or any
existing metric implementation - a metric only needs to match
ai.evaluation.models.Metric's shape (`.name`, `.compute(case)`) to be
usable here, mirroring this project's existing Protocol-based
extensibility convention (ai.retrieval.retriever.Retriever,
ai.reranking.reranker.Reranker).
"""
import logging

from ai.evaluation.models import BenchmarkResult, EvaluationDataset, Metric, MetricResult

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Runs every configured Metric over every case in an
    EvaluationDataset and aggregates each metric's per-case values
    (by arithmetic mean) into a dataset-level MetricResult.
    """

    def __init__(self, metrics: list[Metric]):
        if not metrics:
            raise ValueError("BenchmarkRunner requires at least one metric.")
        self.metrics = metrics

    def run(self, dataset: EvaluationDataset) -> BenchmarkResult:
        """
        Evaluate every case in `dataset` against every configured
        metric. An empty dataset is a valid input: it returns a
        BenchmarkResult with case_count=0 and a 0.0-valued
        MetricResult per metric, rather than raising.
        """
        if not dataset.cases:
            logger.info(
                "Benchmark dataset '%s' has no cases; returning zero-valued results.",
                dataset.name,
            )
            return BenchmarkResult(
                dataset_name=dataset.name,
                case_count=0,
                metric_results=tuple(
                    MetricResult(
                        metric_name=metric.name, value=0.0,
                        details={"case_count": 0},
                    )
                    for metric in self.metrics
                ),
                per_case_results=(),
            )

        per_case_results: list[tuple[MetricResult, ...]] = []
        scores_by_metric: dict[str, list[float]] = {
            metric.name: [] for metric in self.metrics
        }

        for case in dataset.cases:
            case_results = []
            for metric in self.metrics:
                result = metric.compute(case)
                case_results.append(result)
                scores_by_metric.setdefault(result.metric_name, []).append(
                    result.value,
                )
            per_case_results.append(tuple(case_results))

        aggregated = tuple(
            MetricResult(
                metric_name=metric_name,
                value=sum(values) / len(values) if values else 0.0,
                details={"case_count": len(values), "scores": tuple(values)},
            )
            for metric_name, values in scores_by_metric.items()
        )

        logger.info(
            "Benchmark '%s' evaluated %s case(s) against %s metric(s).",
            dataset.name, len(dataset.cases), len(self.metrics),
        )

        return BenchmarkResult(
            dataset_name=dataset.name,
            case_count=len(dataset.cases),
            metric_results=aggregated,
            per_case_results=tuple(per_case_results),
        )

    def compare(
        self,
        baseline: EvaluationDataset,
        treatment: EvaluationDataset,
    ) -> dict:
        """
        Run this runner's metrics over two parallel datasets (e.g.
        baseline retrieval vs. reranked retrieval for the same
        queries) and return both results plus the per-metric delta
        (treatment - baseline).

        Makes no assumption about how `treatment` was produced - it
        only needs to be another EvaluationDataset of the same case
        type as `baseline`, so this same method compares a reranker
        against a baseline retriever, two different retrievers, or two
        different top_k values, without any reranker-specific logic.
        """
        baseline_result = self.run(baseline)
        treatment_result = self.run(treatment)

        baseline_by_name = {
            result.metric_name: result.value
            for result in baseline_result.metric_results
        }
        treatment_by_name = {
            result.metric_name: result.value
            for result in treatment_result.metric_results
        }

        delta = {
            name: treatment_by_name[name] - baseline_by_name.get(name, 0.0)
            for name in treatment_by_name
        }

        return {
            "baseline": baseline_result,
            "treatment": treatment_result,
            "delta": delta,
        }
