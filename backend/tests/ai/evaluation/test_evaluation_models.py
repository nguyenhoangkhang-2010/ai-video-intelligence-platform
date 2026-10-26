import pytest

from ai.evaluation.models import (
    BenchmarkResult,
    EvaluationDataset,
    GenerationEvaluationCase,
    Metric,
    MetricResult,
    RAGEvaluationCase,
    RetrievalEvaluationCase,
)


def test_retrieval_evaluation_case_is_frozen():
    case = RetrievalEvaluationCase(
        query="q", retrieved_ids=("a", "b"), relevant_ids=frozenset({"a"}),
    )
    with pytest.raises(Exception):
        case.query = "changed"


def test_retrieval_evaluation_case_defaults_are_empty():
    case = RetrievalEvaluationCase(query="q", retrieved_ids=())

    assert case.relevant_ids == frozenset()
    assert case.graded_relevance == {}
    assert case.metadata == {}


def test_rag_evaluation_case_defaults():
    case = RAGEvaluationCase(question="q", answer="a")

    assert case.retrieved_contexts == ()
    assert case.reference_answer is None


def test_generation_evaluation_case_holds_candidate_and_reference():
    case = GenerationEvaluationCase(candidate="c", reference="r")

    assert case.candidate == "c"
    assert case.reference == "r"


def test_evaluation_dataset_holds_named_cases():
    cases = (GenerationEvaluationCase(candidate="c", reference="r"),)
    dataset = EvaluationDataset(name="my_dataset", cases=cases)

    assert dataset.name == "my_dataset"
    assert dataset.cases == cases


def test_metric_result_defaults_to_empty_details():
    result = MetricResult(metric_name="m", value=0.5)

    assert result.details == {}


def test_benchmark_result_defaults_to_empty_per_case_results():
    result = BenchmarkResult(dataset_name="ds", case_count=0, metric_results=())

    assert result.per_case_results == ()


class _ConformingMetric:
    name = "fake"

    def compute(self, case):
        return MetricResult(metric_name="fake", value=1.0)


def test_metric_protocol_recognizes_conforming_class_via_isinstance():
    assert isinstance(_ConformingMetric(), Metric)


def test_metric_protocol_rejects_non_conforming_object():
    assert not isinstance(object(), Metric)
