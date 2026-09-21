from unittest.mock import MagicMock

from ai.evaluation.metrics.generation import BERTScoreMetric, RougeMetric
from ai.evaluation.models import GenerationEvaluationCase


def test_rouge_metric_scores_identical_text_as_one():
    metric = RougeMetric(rouge_type="rouge1")
    case = GenerationEvaluationCase(candidate="the cat sat", reference="the cat sat")

    result = metric.compute(case)

    assert metric.name == "rouge_rouge1"
    assert result.value == 1.0
    assert result.details["kind"] == "deterministic"


def test_rouge_metric_reports_all_configured_rouge_scores_in_details():
    metric = RougeMetric(rouge_type="rougeL")
    case = GenerationEvaluationCase(candidate="a b c", reference="a b c")

    result = metric.compute(case)

    assert "rougeL" in result.details


def test_bertscore_metric_never_loads_model_at_construction_time():
    mock_evaluator = MagicMock()
    metric = BERTScoreMetric(evaluator=mock_evaluator)

    mock_evaluator.score.assert_not_called()
    assert metric.name == "bertscore_f1"


def test_bertscore_metric_delegates_to_evaluator_and_extracts_f1():
    mock_evaluator = MagicMock()
    mock_evaluator.score.return_value = {
        "precision": [0.9], "recall": [0.8], "f1": [0.85],
    }
    metric = BERTScoreMetric(evaluator=mock_evaluator)
    case = GenerationEvaluationCase(candidate="generated", reference="reference")

    result = metric.compute(case)

    mock_evaluator.score.assert_called_once_with(["generated"], ["reference"])
    assert result.value == 0.85
    assert result.details["kind"] == "model_based"
    assert result.details["precision"] == 0.9
    assert result.details["recall"] == 0.8


def test_bertscore_metric_handles_empty_score_lists_gracefully():
    mock_evaluator = MagicMock()
    mock_evaluator.score.return_value = {"precision": [], "recall": [], "f1": []}
    metric = BERTScoreMetric(evaluator=mock_evaluator)
    case = GenerationEvaluationCase(candidate="x", reference="y")

    result = metric.compute(case)

    assert result.value == 0.0
