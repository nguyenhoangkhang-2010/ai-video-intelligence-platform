"""
Run the offline AI-quality evaluation framework (ai/evaluation/) against
this deployment's REAL retrieval stack and REAL RAG pipeline for one
already-processed video.

This is the "runner" half of the evaluation framework: ai/evaluation/
already provides the metric implementations (Precision@K, Recall@K,
MRR, NDCG, RAG faithfulness/relevance) and a generic BenchmarkRunner,
but production code never calls them (deliberately - evaluation must
stay offline and out of the request path). Nothing here changes that;
this script only wires those existing metrics to whatever retriever/
pipeline you point it at.

IMPORTANT - this script does NOT ship with a labeled evaluation
dataset, and does not invent one. Retrieval evaluation needs a set of
(query, relevant_chunk_ids) pairs that someone who has actually
watched the target video authored by hand - fabricating those
judgments would produce a meaningless (and dishonest) number. See
ai/evaluation/fixtures/example_retrieval_queries.json for the exact
schema this script expects; copy it and fill in real judgments for a
real video's real vector_ids (see `list-chunks` below) to get a real
score. RAG evaluation only needs questions (no ground truth answers
required for the deterministic metrics), so
ai/evaluation/fixtures/example_rag_questions.json is directly usable
as a starting point.

Usage (from backend/, PYTHONPATH set so `app`/`ai` are importable -
same convention as scripts/rebuild_faiss_index.py):

    # See a video's chunks (vector_id + text) to help you write
    # ground-truth relevance judgments.
    python scripts/run_evaluation.py list-chunks --video-id 1

    # Retrieval quality: dense-only baseline vs. this deployment's
    # live retrieval config (hybrid + reranking, if enabled) -
    # mirrors app/api/deps.py::get_rag_pipeline's construction exactly.
    python scripts/run_evaluation.py retrieval --video-id 1 \\
        --fixture ai/evaluation/fixtures/example_retrieval_queries.json

    # RAG quality: real RAGPipeline.ask() calls, scored with the
    # deterministic (no-LLM-call) lexical-overlap metrics.
    python scripts/run_evaluation.py rag --video-id 1 \\
        --fixture ai/evaluation/fixtures/example_rag_questions.json
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from ai.evaluation.benchmark import BenchmarkRunner
from ai.evaluation.metrics.retrieval import (
    MeanReciprocalRank,
    NDCGAtK,
    PrecisionAtK,
    RecallAtK,
    case_from_retrieval_results,
)
from ai.evaluation.models import EvaluationDataset, RAGEvaluationCase
from ai.evaluation.rag_eval import (
    DeterministicAnswerRelevance,
    DeterministicContextRelevance,
    DeterministicFaithfulness,
)
from ai.retrieval.dense_retriever import DenseRetriever
from ai.retrieval.hybrid_search import HybridRetriever
from ai.retrieval.pipeline import RetrievalPipeline
from ai.retrieval.sparse_retriever import SparseRetriever
from app.config.settings import settings
from app.database.session import SessionLocal
from app.pipelines.rag_pipeline import RAGPipeline
from app.repositories.embedding import EmbeddingRepository
from app.services.embedding import EmbeddingService
from app.services.semantic_search import SemanticSearchService

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("run_evaluation")

DEFAULT_TOP_K = 5


def _build_retrieval_pipelines(embedding_repository: EmbeddingRepository):
    """
    Baseline = dense-only (what RAG looked like before this project's
    hybrid+reranking wiring existed). Treatment = exactly what
    app/api/deps.py::get_rag_pipeline builds today, so `retrieval
    --video-id ...` measures the real, current production
    configuration - not a stand-in for it.
    """
    semantic_search_service = SemanticSearchService(
        embedding_repository=embedding_repository,
    )
    dense = DenseRetriever(semantic_search_service=semantic_search_service)
    baseline = RetrievalPipeline(retriever=dense)

    treatment_retriever = dense
    if settings.retrieval.hybrid_enabled:
        treatment_retriever = HybridRetriever(
            retrievers=[dense, SparseRetriever(embedding_repository=embedding_repository)],
        )

    reranker = None
    if settings.retrieval.reranking_enabled:
        try:
            from ai.reranking.cross_encoder import CrossEncoderReranker

            reranker = CrossEncoderReranker()
        except Exception:
            logger.warning(
                "Cross-encoder reranker unavailable - treatment pipeline "
                "will run hybrid retrieval without reranking.",
                exc_info=True,
            )

    treatment = RetrievalPipeline(retriever=treatment_retriever, reranker=reranker)
    return baseline, treatment


def cmd_list_chunks(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        rows = EmbeddingRepository(db).get_by_video_id(args.video_id)
    finally:
        db.close()

    if not rows:
        print(f"No embeddings found for video {args.video_id}. Has it finished processing?")
        return

    for row in rows:
        preview = row.chunk_text[:100].replace("\n", " ")
        print(f"[{row.chunk_index}] vector_id={row.vector_id!r}  {preview!r}")


def cmd_retrieval(args: argparse.Namespace) -> None:
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    if not fixture:
        print("Fixture file has no cases - nothing to evaluate.")
        return

    db = SessionLocal()
    try:
        embedding_repository = EmbeddingRepository(db)
        baseline_pipeline, treatment_pipeline = _build_retrieval_pipelines(embedding_repository)

        baseline_cases = []
        treatment_cases = []
        for entry in fixture:
            query = entry["query"]
            relevant_ids = entry.get("relevant_chunk_ids", [])
            baseline_results = baseline_pipeline.retrieve(
                query=query, video_id=args.video_id, top_k=args.top_k,
            )
            treatment_results = treatment_pipeline.retrieve(
                query=query, video_id=args.video_id, top_k=args.top_k,
            )
            baseline_cases.append(case_from_retrieval_results(query, baseline_results, relevant_ids))
            treatment_cases.append(case_from_retrieval_results(query, treatment_results, relevant_ids))
    finally:
        db.close()

    metrics = [
        PrecisionAtK(args.top_k),
        RecallAtK(args.top_k),
        MeanReciprocalRank(),
        NDCGAtK(args.top_k),
    ]
    runner = BenchmarkRunner(metrics)
    comparison = runner.compare(
        baseline=EvaluationDataset(name="dense-only (baseline)", cases=tuple(baseline_cases)),
        treatment=EvaluationDataset(name="live retrieval config (treatment)", cases=tuple(treatment_cases)),
    )

    _print_comparison(comparison, case_count=len(fixture))


def cmd_rag(args: argparse.Namespace) -> None:
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    if not fixture:
        print("Fixture file has no questions - nothing to evaluate.")
        return

    db = SessionLocal()
    try:
        embedding_repository = EmbeddingRepository(db)
        embedding_service = EmbeddingService(embedding_repository)
        semantic_search_service = SemanticSearchService(embedding_repository=embedding_repository)
        pipeline = RAGPipeline(
            semantic_search_service=semantic_search_service,
            embedding_service=embedding_service,
        )

        cases = []
        for entry in fixture:
            question = entry["question"]
            result = pipeline.ask(video_id=args.video_id, query=question)
            if result.status != "answered":
                print(f"[skip] {question!r} -> status={result.status!r} (no answer to score)")
                continue
            cases.append(
                RAGEvaluationCase(
                    question=question,
                    answer=result.answer or "",
                    retrieved_contexts=tuple(source.chunk_text for source in result.sources),
                    reference_answer=entry.get("reference_answer"),
                ),
            )
    finally:
        db.close()

    if not cases:
        print("No question produced a groundable answer - nothing to score.")
        return

    metrics = [
        DeterministicFaithfulness(),
        DeterministicAnswerRelevance(),
        DeterministicContextRelevance(),
    ]
    runner = BenchmarkRunner(metrics)
    result = runner.run(EvaluationDataset(name=f"video {args.video_id} RAG", cases=tuple(cases)))

    print(f"\nRAG evaluation - video {args.video_id} ({result.case_count} answered question(s))")
    print(
        "NOTE: these are lexical-overlap proxies (ai.evaluation.rag_eval."
        "Deterministic*), not a semantic judgment - see that module's "
        "docstring. Enable EVALUATION_LLM_JUDGE_ENABLED and use the "
        "LLMJudge* variants for a model-based score."
    )
    for metric_result in result.metric_results:
        print(f"  {metric_result.metric_name:<28} {metric_result.value:.3f}")


def _print_comparison(comparison: dict, case_count: int) -> None:
    baseline, treatment, delta = comparison["baseline"], comparison["treatment"], comparison["delta"]
    print(f"\nRetrieval evaluation - {case_count} quer{'y' if case_count == 1 else 'ies'}")
    print(f"{'metric':<14}{'baseline':>12}{'treatment':>12}{'delta':>12}")

    baseline_by_name = {r.metric_name: r.value for r in baseline.metric_results}
    treatment_by_name = {r.metric_name: r.value for r in treatment.metric_results}
    for name in treatment_by_name:
        b, t, d = baseline_by_name.get(name, 0.0), treatment_by_name[name], delta[name]
        sign = "+" if d >= 0 else ""
        print(f"{name:<14}{b:>12.3f}{t:>12.3f}{sign}{d:>11.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-chunks", help="Print a video's chunks to help author ground truth.")
    list_parser.add_argument("--video-id", type=int, required=True)
    list_parser.set_defaults(func=cmd_list_chunks)

    retrieval_parser = subparsers.add_parser("retrieval", help="Score retrieval quality: baseline vs. live config.")
    retrieval_parser.add_argument("--video-id", type=int, required=True)
    retrieval_parser.add_argument("--fixture", required=True, help="Path to a retrieval-cases JSON file.")
    retrieval_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    retrieval_parser.set_defaults(func=cmd_retrieval)

    rag_parser = subparsers.add_parser("rag", help="Score grounded-answer quality for real RAG calls.")
    rag_parser.add_argument("--video-id", type=int, required=True)
    rag_parser.add_argument("--fixture", required=True, help="Path to a questions JSON file.")
    rag_parser.set_defaults(func=cmd_rag)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
