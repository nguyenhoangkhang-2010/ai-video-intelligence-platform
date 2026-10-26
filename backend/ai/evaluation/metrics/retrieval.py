"""
Deterministic retrieval/reranking quality metrics: Precision@K,
Recall@K, (Mean) Reciprocal Rank, and NDCG@K.

All functions operate on plain, generic identifiers (retrieved_ids /
relevant_ids) - they know nothing about videos, chunks, embeddings, or
any other domain concept, so the exact same functions evaluate a
baseline retriever, a hybrid retriever, or a reranked ranking without
any changes. This also means they are usable completely independently
of ai.retrieval.pipeline.RetrievalPipeline; `case_from_retrieval_results`
below is the (optional) bridge from that pipeline's own RetrievalResult
objects to the generic case shape these functions consume.

Shared behavior across every function here:
- Tolerates empty retrieved_ids / empty relevant_ids without raising
  (returns 0.0) - a query with no candidates or no ground truth is a
  valid, if degenerate, input; never divides by zero.
- Deduplicates retrieved_ids first, keeping each id's first (best-
  ranked) occurrence, so a retriever/reranker that accidentally
  returns the same id twice can't inflate its own score.
- Supports arbitrary K (K larger than the retrieved list is simply
  clamped by slicing; K <= 0 returns 0.0).

Reciprocal Rank / "MRR": the function/metric here computes a single
case's reciprocal rank. The conventional dataset-level *Mean*
Reciprocal Rank is the mean of these per-case values across a
dataset - exactly what ai.evaluation.benchmark.BenchmarkRunner
computes when it aggregates this metric over many cases.
"""
import math
from typing import Iterable

from ai.evaluation.models import MetricResult, RetrievalEvaluationCase


def _dedupe_preserve_order(ids: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in ids:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def precision_at_k(
    retrieved_ids: Iterable[str],
    relevant_ids: Iterable[str],
    k: int,
) -> float:
    """Fraction of the top-K (deduplicated) retrieved ids that are relevant."""
    if k <= 0:
        return 0.0

    ranked = _dedupe_preserve_order(retrieved_ids)[:k]
    if not ranked:
        return 0.0

    relevant_set = set(relevant_ids)
    hits = sum(1 for doc_id in ranked if doc_id in relevant_set)

    return hits / len(ranked)


def recall_at_k(
    retrieved_ids: Iterable[str],
    relevant_ids: Iterable[str],
    k: int,
) -> float:
    """Fraction of all relevant ids that appear in the top-K retrieved ids."""
    relevant_set = set(relevant_ids)
    if not relevant_set or k <= 0:
        return 0.0

    ranked = _dedupe_preserve_order(retrieved_ids)[:k]
    hits = sum(1 for doc_id in ranked if doc_id in relevant_set)

    return hits / len(relevant_set)


def reciprocal_rank(
    retrieved_ids: Iterable[str],
    relevant_ids: Iterable[str],
) -> float:
    """1 / (rank of the first relevant id), or 0.0 if none is retrieved."""
    relevant_set = set(relevant_ids)
    if not relevant_set:
        return 0.0

    for position, doc_id in enumerate(_dedupe_preserve_order(retrieved_ids), start=1):
        if doc_id in relevant_set:
            return 1.0 / position

    return 0.0


def _relevance_of(
    doc_id: str,
    relevant_ids: set[str],
    graded_relevance: dict[str, float],
) -> float:
    if doc_id in graded_relevance:
        return float(graded_relevance[doc_id])
    return 1.0 if doc_id in relevant_ids else 0.0


def _gain(relevance: float) -> float:
    return (2.0 ** relevance) - 1.0


def ndcg_at_k(
    retrieved_ids: Iterable[str],
    relevant_ids: Iterable[str],
    k: int,
    graded_relevance: dict[str, float] | None = None,
) -> float:
    """
    Normalized Discounted Cumulative Gain over the top-K retrieved ids.

    Uses the standard exponential-gain formulation
    (gain = 2**relevance - 1), which reduces exactly to binary NDCG
    when every relevance grade is 0 or 1 (the default when
    `graded_relevance` is not supplied - membership in `relevant_ids`
    alone is then treated as grade 1).
    """
    if k <= 0:
        return 0.0

    relevant_set = set(relevant_ids)
    graded_relevance = graded_relevance or {}
    ranked = _dedupe_preserve_order(retrieved_ids)[:k]

    dcg = sum(
        _gain(_relevance_of(doc_id, relevant_set, graded_relevance))
        / math.log2(position + 1)
        for position, doc_id in enumerate(ranked, start=1)
    )

    known_relevant_ids = relevant_set | set(graded_relevance)
    ideal_relevances = sorted(
        (
            _relevance_of(doc_id, relevant_set, graded_relevance)
            for doc_id in known_relevant_ids
        ),
        reverse=True,
    )[:k]

    idcg = sum(
        _gain(relevance) / math.log2(position + 1)
        for position, relevance in enumerate(ideal_relevances, start=1)
    )

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


class PrecisionAtK:
    """Metric wrapper: Precision@K over a RetrievalEvaluationCase."""

    def __init__(self, k: int):
        self.k = k
        self.name = f"precision@{k}"

    def compute(self, case: RetrievalEvaluationCase) -> MetricResult:
        value = precision_at_k(case.retrieved_ids, case.relevant_ids, self.k)
        return MetricResult(
            metric_name=self.name, value=value, details={"k": self.k},
        )


class RecallAtK:
    """Metric wrapper: Recall@K over a RetrievalEvaluationCase."""

    def __init__(self, k: int):
        self.k = k
        self.name = f"recall@{k}"

    def compute(self, case: RetrievalEvaluationCase) -> MetricResult:
        value = recall_at_k(case.retrieved_ids, case.relevant_ids, self.k)
        return MetricResult(
            metric_name=self.name, value=value, details={"k": self.k},
        )


class MeanReciprocalRank:
    """
    Metric wrapper producing one case's reciprocal rank. See the
    module docstring: the dataset-level *mean* ("MRR" in the
    conventional sense) is what BenchmarkRunner computes when
    aggregating this metric's per-case values across a dataset.
    """

    name = "mrr"

    def compute(self, case: RetrievalEvaluationCase) -> MetricResult:
        value = reciprocal_rank(case.retrieved_ids, case.relevant_ids)
        return MetricResult(metric_name=self.name, value=value)


class NDCGAtK:
    """Metric wrapper: NDCG@K over a RetrievalEvaluationCase."""

    def __init__(self, k: int):
        self.k = k
        self.name = f"ndcg@{k}"

    def compute(self, case: RetrievalEvaluationCase) -> MetricResult:
        value = ndcg_at_k(
            case.retrieved_ids, case.relevant_ids, self.k,
            case.graded_relevance,
        )
        return MetricResult(
            metric_name=self.name, value=value, details={"k": self.k},
        )


def case_from_retrieval_results(
    query: str,
    results,
    relevant_ids: Iterable[str],
    graded_relevance: dict[str, float] | None = None,
) -> RetrievalEvaluationCase:
    """
    Build a RetrievalEvaluationCase from a ranked list of
    ai.retrieval.retriever.RetrievalResult (as returned by
    RetrievalPipeline.retrieve / any Retriever / any Reranker).

    This is the one place evaluation code depends on the retrieval
    layer's result type - the dependency only ever points this
    direction; the retrieval layer never imports anything from
    ai.evaluation, so production retrieval/reranking stays unaware
    evaluation exists.
    """
    return RetrievalEvaluationCase(
        query=query,
        retrieved_ids=tuple(result.id for result in results),
        relevant_ids=frozenset(relevant_ids),
        graded_relevance=dict(graded_relevance or {}),
    )
