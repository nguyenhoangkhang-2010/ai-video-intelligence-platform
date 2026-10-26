"""
Metric-conforming wrappers around ai.evaluation.rouge / ai.evaluation.
bertscore for use with GenerationEvaluationCase and BenchmarkRunner.

ROUGE (RougeMetric) is deterministic and always available - a
lightweight, pure-Python dependency already installed, safe to import
eagerly. BERTScore (BERTScoreMetric) is model-based and optional: the
underlying transformer model is only loaded the first time a
BERTScoreMetric instance actually computes a score (see
ai.evaluation.bertscore.BERTScoreEvaluator), never at import time.
"""
from ai.evaluation.bertscore import BERTScoreEvaluator
from ai.evaluation.models import GenerationEvaluationCase, MetricResult
from ai.evaluation.rouge import RougeScorer


class RougeMetric:
    """Deterministic generation metric: ROUGE F-measure for one rouge type."""

    def __init__(
        self,
        rouge_type: str = "rougeL",
        scorer: RougeScorer | None = None,
    ):
        self.rouge_type = rouge_type
        self.name = f"rouge_{rouge_type}"
        self._scorer = scorer or RougeScorer(rouge_types=[rouge_type])

    def compute(self, case: GenerationEvaluationCase) -> MetricResult:
        scores = self._scorer.score(case.candidate, case.reference)
        return MetricResult(
            metric_name=self.name,
            value=scores[self.rouge_type],
            details={"kind": "deterministic", **scores},
        )


class BERTScoreMetric:
    """
    Model-based generation metric (BERTScore F1). Constructing this
    class never loads a model - only the first `.compute()` call does
    (via BERTScoreEvaluator's own lazy loading).
    """

    name = "bertscore_f1"

    def __init__(self, evaluator: BERTScoreEvaluator | None = None):
        self._evaluator = evaluator or BERTScoreEvaluator()

    def compute(self, case: GenerationEvaluationCase) -> MetricResult:
        scores = self._evaluator.score([case.candidate], [case.reference])
        value = scores["f1"][0] if scores["f1"] else 0.0
        return MetricResult(
            metric_name=self.name,
            value=value,
            details={
                "kind": "model_based",
                "precision": scores["precision"][0] if scores["precision"] else None,
                "recall": scores["recall"][0] if scores["recall"] else None,
            },
        )
