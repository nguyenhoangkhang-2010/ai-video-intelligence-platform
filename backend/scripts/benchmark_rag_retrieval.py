"""
Real RAG retrieval evaluation against this deployment's actual data.

Unlike ai/evaluation/fixtures/golden_dataset.json (a synthetic
regression fixture proving the evaluation framework's own math is
correct - see tests/ai/evaluation/test_golden_dataset.py), this script
scores the REAL retrieval stack (real BGE-M3 embeddings already in the
FAISS index, real BM25, real RRF fusion, real cross-encoder reranker)
against ai/evaluation/fixtures/real_ground_truth.json - real
transcript text pulled from this project's own dev database, with
real relevance judgments a human made after reading that text.

Methodology note (read this before trusting the numbers): this
project's real dev dataset has only 6 distinct short-form video
transcripts, each producing exactly one embedding chunk - there is no
real multi-chunk, long-form video in this deployment to evaluate
WITHIN-document chunk ranking. So this benchmark instead pools those 6
real documents into one evaluation corpus and asks which of the 6 best
answers each real query - a genuine CROSS-document retrieval
evaluation, not the within-video search the product actually runs at
request time. It does this by substituting only the data-access layer
(a shim EmbeddingRepository returning all 6 real rows for any
video_id) in front of the UNCHANGED, real DenseRetriever/
SparseRetriever/HybridRetriever/RetrievalPipeline/CrossEncoderReranker
classes - no retrieval/ranking code is modified or mocked.

10 queries over 6 documents is not statistically significant. Treat
every number this script prints as a real but small, exploratory
measurement, not a production quality guarantee - see
docs/benchmarks/rag-evaluation.md for the full writeup and caveats.

Usage (from backend/, PYTHONPATH set so `app`/`ai` are importable):
    python scripts/benchmark_rag_retrieval.py
"""
import argparse
import json
import logging
import time
from pathlib import Path

from ai.evaluation.benchmark import BenchmarkRunner
from ai.evaluation.metrics.retrieval import (
    MeanReciprocalRank,
    NDCGAtK,
    PrecisionAtK,
    RecallAtK,
    case_from_retrieval_results,
)
from ai.evaluation.models import EvaluationDataset
from ai.retrieval.dense_retriever import DenseRetriever
from ai.retrieval.hybrid_search import HybridRetriever
from ai.retrieval.pipeline import RetrievalPipeline
from ai.retrieval.sparse_retriever import SparseRetriever
from app.database.session import SessionLocal
from app.models.embedding import Embedding
from app.repositories.embedding import EmbeddingRepository
from app.services.semantic_search import SemanticSearchService

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("benchmark_rag_retrieval")

FIXTURE_PATH = (
    Path(__file__).parent.parent
    / "ai"
    / "evaluation"
    / "fixtures"
    / "real_ground_truth.json"
)
TOP_K = 5


class _PooledEmbeddingRepository:
    """
    Returns the same fixed set of REAL Embedding rows (fetched once
    from the real dev database by vector_id) regardless of the
    video_id argument - see the module docstring for why. Every other
    EmbeddingRepository method is untouched (delegated to a real
    instance), so anything beyond get_by_video_id still behaves
    exactly as it does in production.
    """

    def __init__(self, db, vector_ids: list[str]):
        self._real = EmbeddingRepository(db)
        self._rows = [
            row
            for vector_id in vector_ids
            for row in [self._real.get_by_vector_id(vector_id)]
            if row is not None
        ]
        missing = set(vector_ids) - {row.vector_id for row in self._rows}
        if missing:
            raise RuntimeError(
                f"real_ground_truth.json references vector_ids not "
                f"found in the real database: {missing}",
            )

    def get_by_video_id(self, video_id: int) -> list[Embedding]:
        return self._rows

    def __getattr__(self, name):
        return getattr(self._real, name)


def _build_pipelines(
    repository: _PooledEmbeddingRepository,
    reranker_models: list[str | None],
):
    semantic_search_service = SemanticSearchService(
        embedding_repository=repository,
    )
    dense = DenseRetriever(semantic_search_service=semantic_search_service)
    sparse = SparseRetriever(embedding_repository=repository)
    hybrid = HybridRetriever(retrievers=[dense, sparse])

    pipelines = {
        "dense_only": RetrievalPipeline(retriever=dense),
        "sparse_only": RetrievalPipeline(retriever=sparse),
        "hybrid": RetrievalPipeline(retriever=hybrid),
    }

    # One "hybrid + reranking" arm per reranker model (None = the
    # configured CROSS_ENCODER_MODEL), so models can be compared on the
    # same real queries.
    for model_name in reranker_models:
        arm = (
            "hybrid_plus_reranking"
            if model_name is None
            else f"rerank:{model_name.split('/')[-1]}"
        )
        try:
            from ai.reranking.cross_encoder import CrossEncoderReranker

            reranker = CrossEncoderReranker(model_name=model_name)
            pipelines[arm] = RetrievalPipeline(
                retriever=hybrid, reranker=reranker,
            )
        except Exception:
            logger.warning(
                "Cross-encoder reranker %s unavailable - skipping the "
                "%s arm.",
                model_name or "(configured)",
                arm,
                exc_info=True,
            )

    return pipelines


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score the real retrieval stack against a ground-truth fixture.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=FIXTURE_PATH,
        help=(
            "documents/queries JSON (default: real_ground_truth.json). "
            "Use a human-reviewed set from scripts/review_eval_questions.py."
        ),
    )
    parser.add_argument(
        "--reranker-models",
        default="",
        help=(
            "comma-separated cross-encoder models to compare; empty = "
            "only the configured CROSS_ENCODER_MODEL"
        ),
    )
    args = parser.parse_args()
    reranker_models: list[str | None] = [
        name.strip() for name in args.reranker_models.split(",") if name.strip()
    ] or [None]

    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    documents = fixture["documents"]
    queries = fixture["queries"]
    vector_ids = [doc["vector_id"] for doc in documents]

    db = SessionLocal()
    try:
        repository = _PooledEmbeddingRepository(db, vector_ids)
        pipelines = _build_pipelines(repository, reranker_models)

        metrics = [
            PrecisionAtK(TOP_K),
            RecallAtK(TOP_K),
            MeanReciprocalRank(),
            NDCGAtK(TOP_K),
        ]
        runner = BenchmarkRunner(metrics)

        results_by_pipeline = {}
        timing_by_pipeline = {}

        for name, pipeline in pipelines.items():
            cases = []
            start = time.perf_counter()
            for entry in queries:
                results = pipeline.retrieve(
                    query=entry["query"],
                    video_id=0,  # ignored by the pooled shim
                    top_k=TOP_K,
                )
                cases.append(
                    case_from_retrieval_results(
                        entry["query"], results, entry["relevant_vector_ids"],
                    ),
                )
            elapsed = time.perf_counter() - start
            timing_by_pipeline[name] = elapsed / len(queries) if queries else 0.0

            dataset = EvaluationDataset(name=name, cases=tuple(cases))
            results_by_pipeline[name] = runner.run(dataset)

        print(f"\nReal RAG retrieval benchmark - {len(queries)} real queries, "
              f"{len(documents)} real documents, top_k={TOP_K}\n")
        header = f"{'metric':<14}" + "".join(f"{name:>22}" for name in results_by_pipeline)
        print(header)
        metric_names = [m.name for m in metrics]
        for metric_name in metric_names:
            row = f"{metric_name:<14}"
            for name, result in results_by_pipeline.items():
                value = next(
                    (r.value for r in result.metric_results if r.metric_name == metric_name),
                    float("nan"),
                )
                row += f"{value:>22.3f}"
            print(row)

        print(f"\n{'avg query latency (s)':<14}", end="")
        for name in results_by_pipeline:
            print(f"{timing_by_pipeline[name]:>22.4f}", end="")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
