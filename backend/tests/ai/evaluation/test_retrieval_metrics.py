from ai.evaluation.metrics.retrieval import (
    MeanReciprocalRank,
    NDCGAtK,
    PrecisionAtK,
    RecallAtK,
    case_from_retrieval_results,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from ai.evaluation.models import RetrievalEvaluationCase


# ---- precision_at_k ----

def test_precision_at_k_counts_relevant_hits_in_top_k():
    retrieved = ["a", "b", "c", "d"]
    relevant = {"a", "c"}

    assert precision_at_k(retrieved, relevant, k=4) == 0.5


def test_precision_at_k_clamps_k_larger_than_retrieved_length():
    retrieved = ["a", "b"]
    relevant = {"a"}

    assert precision_at_k(retrieved, relevant, k=10) == 0.5


def test_precision_at_k_returns_zero_for_empty_retrieved():
    assert precision_at_k([], {"a"}, k=5) == 0.0


def test_precision_at_k_returns_zero_for_non_positive_k():
    assert precision_at_k(["a"], {"a"}, k=0) == 0.0
    assert precision_at_k(["a"], {"a"}, k=-1) == 0.0


def test_precision_at_k_deduplicates_retrieved_ids():
    # "a" appears twice - must count once, not double.
    retrieved = ["a", "a", "b"]
    relevant = {"a"}

    assert precision_at_k(retrieved, relevant, k=3) == 1 / 2


# ---- recall_at_k ----

def test_recall_at_k_counts_fraction_of_relevant_found():
    retrieved = ["a", "x", "y"]
    relevant = {"a", "b", "c"}

    assert recall_at_k(retrieved, relevant, k=3) == 1 / 3


def test_recall_at_k_returns_zero_for_empty_relevant_set():
    assert recall_at_k(["a", "b"], set(), k=5) == 0.0


def test_recall_at_k_returns_zero_for_non_positive_k():
    assert recall_at_k(["a"], {"a"}, k=0) == 0.0


def test_recall_at_k_respects_k_boundary():
    retrieved = ["a", "b", "c"]
    relevant = {"c"}

    assert recall_at_k(retrieved, relevant, k=2) == 0.0
    assert recall_at_k(retrieved, relevant, k=3) == 1.0


# ---- reciprocal_rank ----

def test_reciprocal_rank_returns_inverse_of_first_hit_position():
    retrieved = ["x", "y", "a", "b"]
    relevant = {"a"}

    assert reciprocal_rank(retrieved, relevant) == 1 / 3


def test_reciprocal_rank_returns_one_for_first_position_hit():
    assert reciprocal_rank(["a", "b"], {"a"}) == 1.0


def test_reciprocal_rank_returns_zero_when_no_hit():
    assert reciprocal_rank(["x", "y"], {"a"}) == 0.0


def test_reciprocal_rank_returns_zero_for_empty_retrieved():
    assert reciprocal_rank([], {"a"}) == 0.0


def test_reciprocal_rank_returns_zero_for_empty_relevant_set():
    assert reciprocal_rank(["a", "b"], set()) == 0.0


def test_reciprocal_rank_ignores_duplicate_earlier_occurrences():
    # "x" (irrelevant) repeated shouldn't shift "a"'s effective rank
    # past its true (deduplicated) position.
    retrieved = ["x", "x", "a"]
    relevant = {"a"}

    assert reciprocal_rank(retrieved, relevant) == 1 / 2


# ---- ndcg_at_k ----

def test_ndcg_at_k_returns_one_for_perfect_ranking():
    retrieved = ["a", "b", "c"]
    relevant = {"a", "b", "c"}

    assert ndcg_at_k(retrieved, relevant, k=3) == 1.0


def test_ndcg_at_k_returns_zero_for_no_relevant_hits():
    retrieved = ["x", "y", "z"]
    relevant = {"a"}

    assert ndcg_at_k(retrieved, relevant, k=3) == 0.0


def test_ndcg_at_k_returns_zero_for_empty_relevance_set_and_no_grades():
    assert ndcg_at_k(["a", "b"], set(), k=2) == 0.0


def test_ndcg_at_k_returns_zero_for_non_positive_k():
    assert ndcg_at_k(["a"], {"a"}, k=0) == 0.0


def test_ndcg_at_k_penalizes_lower_ranked_relevant_items():
    relevant = {"a"}
    # "a" first -> ideal ranking -> NDCG 1.0
    ndcg_first = ndcg_at_k(["a", "x", "y"], relevant, k=3)
    # "a" last -> discounted -> NDCG < 1.0
    ndcg_last = ndcg_at_k(["x", "y", "a"], relevant, k=3)

    assert ndcg_first == 1.0
    assert 0.0 < ndcg_last < 1.0


def test_ndcg_at_k_supports_graded_relevance():
    retrieved = ["a", "b"]
    relevant = {"a", "b"}
    graded = {"a": 3.0, "b": 1.0}

    # Highly-graded item ("a", grade 3) ranked first -> ideal -> 1.0.
    assert ndcg_at_k(retrieved, relevant, k=2, graded_relevance=graded) == 1.0

    # Reversed order is a worse (but not zero) ranking.
    reversed_ndcg = ndcg_at_k(
        ["b", "a"], relevant, k=2, graded_relevance=graded,
    )
    assert 0.0 < reversed_ndcg < 1.0


# ---- Metric wrapper classes ----

def _case(retrieved, relevant, graded=None):
    return RetrievalEvaluationCase(
        query="q",
        retrieved_ids=tuple(retrieved),
        relevant_ids=frozenset(relevant),
        graded_relevance=graded or {},
    )


def test_precision_at_k_metric_wraps_function_and_names_itself():
    metric = PrecisionAtK(k=2)
    case = _case(["a", "b"], {"a"})

    result = metric.compute(case)

    assert metric.name == "precision@2"
    assert result.metric_name == "precision@2"
    assert result.value == 0.5


def test_recall_at_k_metric_wraps_function_and_names_itself():
    metric = RecallAtK(k=2)
    case = _case(["a", "x"], {"a", "b"})

    result = metric.compute(case)

    assert metric.name == "recall@2"
    assert result.value == 0.5


def test_mean_reciprocal_rank_metric_returns_per_case_reciprocal_rank():
    metric = MeanReciprocalRank()
    case = _case(["x", "a"], {"a"})

    result = metric.compute(case)

    assert metric.name == "mrr"
    assert result.value == 0.5


def test_ndcg_at_k_metric_uses_case_graded_relevance():
    metric = NDCGAtK(k=2)
    case = _case(["a", "b"], {"a", "b"}, graded={"a": 2.0, "b": 1.0})

    result = metric.compute(case)

    assert metric.name == "ndcg@2"
    assert result.value == 1.0


# ---- case_from_retrieval_results ----

class _FakeRetrievalResult:
    def __init__(self, id):
        self.id = id


def test_case_from_retrieval_results_preserves_rank_order():
    results = [_FakeRetrievalResult("a"), _FakeRetrievalResult("b")]

    case = case_from_retrieval_results(
        query="what happened?", results=results, relevant_ids={"a"},
    )

    assert case.query == "what happened?"
    assert case.retrieved_ids == ("a", "b")
    assert case.relevant_ids == frozenset({"a"})


def test_case_from_retrieval_results_accepts_graded_relevance():
    results = [_FakeRetrievalResult("a")]

    case = case_from_retrieval_results(
        query="q", results=results, relevant_ids={"a"},
        graded_relevance={"a": 2.0},
    )

    assert case.graded_relevance == {"a": 2.0}
