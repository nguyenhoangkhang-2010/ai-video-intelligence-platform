"""
Shared, domain-agnostic result and case structures for AI quality
evaluation.

Nothing here mentions a video, a query someone actually asked, a
retrieved chunk's real content, or any other application-specific
value - every structure is generic over IDs/text/scores so the same
types describe a retrieval benchmark, a RAG benchmark, or a generation
benchmark built from entirely different (and, in real use, entirely
synthetic/test-authored) data.

This module is pure data (frozen dataclasses + a structural Protocol)
- it has no dependency on Ollama, embeddings, FAISS, or any other
production runtime component, and production code never imports it.
"""
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    """
    One retrieval (or reranking) evaluation case.

    query             - the query issued to the retriever/reranker.
    retrieved_ids     - ranked document/chunk IDs actually returned,
                        most relevant first.
    relevant_ids      - the ground-truth set of IDs considered
                        relevant to `query` (binary relevance).
    graded_relevance  - optional {id: relevance_grade} map for graded
                        relevance (used by NDCG); an id present here
                        overrides its binary membership in
                        `relevant_ids` for grading purposes. IDs
                        absent from both are treated as not relevant
                        (grade 0).
    metadata          - anything else worth carrying through.
    """

    query: str
    retrieved_ids: tuple[str, ...]
    relevant_ids: frozenset[str] = field(default_factory=frozenset)
    graded_relevance: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RAGEvaluationCase:
    """
    One retrieval-augmented-generation evaluation case.

    question           - the question that was asked.
    answer             - the system's generated answer.
    retrieved_contexts - the context chunks the answer was (supposed
                        to be) grounded in, in retrieval order.
    reference_answer   - optional ground-truth/reference answer, for
                        metrics that need one.
    metadata            - anything else worth carrying through
                        (e.g. evaluator configuration overrides).
    """

    question: str
    answer: str
    retrieved_contexts: tuple[str, ...] = field(default_factory=tuple)
    reference_answer: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationEvaluationCase:
    """
    One free-text generation evaluation case (summary, translation,
    chapter label, quiz/flashcard content, or any other candidate-vs-
    reference comparison).
    """

    candidate: str
    reference: str
    metadata: dict[str, Any] = field(default_factory=dict)


EvaluationCase = (
    RetrievalEvaluationCase | RAGEvaluationCase | GenerationEvaluationCase
)


@dataclass(frozen=True)
class EvaluationDataset:
    """A named, ordered collection of evaluation cases of one kind."""

    name: str
    cases: tuple[EvaluationCase, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricResult:
    """
    The outcome of scoring one metric - either against a single case,
    or as an aggregate produced by BenchmarkRunner across a dataset.

    metric_name - stable identifier for the metric (e.g.
                "precision@5", "rouge_rougeL", "faithfulness_lexical").
    value       - the numeric score.
    details     - metric-specific extra information (e.g. the raw
                per-case scores an aggregate was computed from, or
                whether a RAG metric was "deterministic" vs
                "model_based").
    """

    metric_name: str
    value: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BenchmarkResult:
    """
    Aggregated outcome of running a BenchmarkRunner over an
    EvaluationDataset: one aggregated MetricResult per metric, plus
    (optionally) the raw per-case results for inspection/debugging.
    """

    dataset_name: str
    case_count: int
    metric_results: tuple[MetricResult, ...]
    per_case_results: tuple[tuple[MetricResult, ...], ...] = field(
        default_factory=tuple,
    )
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Metric(Protocol):
    """
    Structural contract for anything that scores a single evaluation
    case and returns a MetricResult.

    A Protocol (not an ABC) - matching this project's existing
    convention for swappable collaborators (ai.retrieval.retriever.
    Retriever, ai.reranking.reranker.Reranker): no inheritance
    required, so a new metric only needs to match this shape to be
    usable by BenchmarkRunner. `name` must be stable across calls
    (BenchmarkRunner aggregates by it).
    """

    name: str

    def compute(self, case: Any) -> MetricResult:
        """Score `case` and return a MetricResult for it."""
        ...
